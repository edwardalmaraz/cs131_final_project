import os
import tempfile
import numba

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from database import *
from pydantic import BaseModel
from scoring.text import score_lyrics
from scoring.pitch import compare_pitch, precompute_ref_pitches
from typing import Optional
import io
import base64
import json

app = FastAPI()

# In-memory cache of pre-analyzed reference pitch windows, keyed by song_id.
# Populated on first request or via POST /songs/{song_id}/precompute_pitch.
_ref_pitch_cache: dict = {}

class song_metadata_update(BaseModel):
    song_title: Optional[str] = None
    artist_name: Optional[str] = None
    album: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    bpm: Optional[int] = None
    sequence_order: Optional[str] = None
    poses: Optional[list] = None


class lyric_score_request(BaseModel):
    song_id: str
    player_id: str
    player_transcript: str

class lyric_score_response(BaseModel):
    player_id: str
    lyric_score: float

class pitch_score_response(BaseModel):
    player_id: str
    pitch_score: float


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/ping", summary="Health check endpoint", tags=["Utility"])
async def ping():
    return {"status": "online"}


# --- Song upload (manual admin use) ---

@app.post("/songs/upload", summary="Uploads a song", tags=["Songs"])
async def upload_song_endpoint(
    song_id: str = Form(...),
    song_title: str = Form(...),
    artist_name: str = Form(...),
    sequence_order: Optional[str] = Form(None),
    poses: Optional[str] = Form(None),  # JSON string of list of pose names
    album: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    genre: Optional[str] = Form(None),
    bpm: Optional[int] = Form(None),
    mp3_file: UploadFile = File(...),
    lyrics_file: UploadFile = File(...),
):
    if not mp3_file.filename.endswith(".mp3"):
        raise HTTPException(status_code=400, detail="mp3_file must be a .mp3")

    try:
        poses_list = json.loads(poses) if poses else []
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="poses must be a valid JSON array")

    mp3_bytes = await mp3_file.read()
    lyrics_text = None
    if lyrics_file is not None:
        lyrics_bytes = await lyrics_file.read()
        lyrics_text = lyrics_bytes.decode("utf-8")

    metadata = upload_song(
        song_id=song_id,
        song_title=song_title,
        artist_name=artist_name,
        mp3_bytes=mp3_bytes,
        sequence_order=sequence_order,
        poses=poses_list,
        lyrics=lyrics_text,
        album=album,
        year=year,
        genre=genre,
        bpm=bpm,
    )
    return {"status": "uploaded", "song": metadata}


# --- Song retrieval (used by Jetson / frontend) ---
@app.get("/songs",  summary="List all songs via song title", tags=["Songs"])
async def get_songs():
    return {"songs": list_songs()}


@app.get("/songs/{song_id}/meta_data", summary="Get Song Metadata", tags=["Songs"])
async def get_song(song_id: str):
    try:
        metadata = get_song_metadata(song_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Song '{song_id}' not found")
    #if lyrics not already in metadata, attempt to fetch and add it before returning
    if "lyrics" not in metadata:
        try:
            metadata["lyrics"] = get_song_lyrics_raw(song_id)
        except Exception:
            metadata["lyrics"] = None
    return metadata

@app.get("/songs/{song_id}/mp3", summary="Stream Song MP3", tags=["Songs"])
async def stream_song_mp3(song_id: str):
    try:
        mp3_bytes = get_song_mp3(song_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"MP3 for '{song_id}' not found")
    return StreamingResponse(
        io.BytesIO(mp3_bytes),
        media_type="audio/mpeg",
        headers={"Content-Disposition": f"attachment; filename={song_id}.mp3"},
    )


@app.patch("/songs/{song_id}/metadata", summary="Update song metadata fields", tags=["Songs"])
async def patch_song_metadata(song_id: str, updates: song_metadata_update):
    try:
        metadata = update_song_metadata(song_id, updates.model_dump(exclude_none=True))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Song '{song_id}' not found")
    return {"status": "updated", "song": metadata}


# Pitch precompute (call once per song after upload) 
@app.post("/songs/{song_id}/precompute_pitch", summary="Pre-analyze reference pitch windows for a song", tags=["Songs"])
async def precompute_pitch_endpoint(song_id: str):
    # Fetch the reference WAV from the database; 404 if the song doesn't exist yet.
    try:
        ref_wav_bytes = get_song_wav(song_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"WAV for '{song_id}' not found")

    # Write WAV bytes to a temp file so precompute_ref_pitches can read it from disk.
    # delete=False keeps the file alive after the context manager closes it.
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as ref_tmp:
        ref_tmp.write(ref_wav_bytes)
        ref_path = ref_tmp.name

    try:
        # Analyze the reference audio into fixed-length pitch windows and store in memory.
        _ref_pitch_cache[song_id] = precompute_ref_pitches(ref_path)
    finally:
        # Always remove the temp file, even if precompute_ref_pitches raises.
        os.unlink(ref_path)

    print(f"[main] precomputed and cached {len(_ref_pitch_cache[song_id])} pitch windows for {song_id}", flush=True)
    return {"status": "cached", "song_id": song_id, "windows": len(_ref_pitch_cache[song_id])}


# --- Scoring ---
@app.post("/score/lyrics", response_model=lyric_score_response, summary="Score player's lyrics against the original song lyrics", tags=["Scoring"])
async def compute_score(request: lyric_score_request):
    lyrics = get_song_lyrics(request.song_id)
    result = score_lyrics(request.player_transcript, lyrics)
    save_score(request.player_id, result, request.song_id)
    return lyric_score_response(player_id=request.player_id, lyric_score=result)


# --- Server recieving Jetson packet (WAV + transcript) to compute final score ---
@app.post("/score/final", summary="Receive WAV + transcript from Jetson to calculate final score", tags=["Scoring"])
async def submit_round(
    song_id: str = Form(...),
    player_id: str = Form(...),
    player_transcript: str = Form(...),
    wav_file: UploadFile = File(...),
    move_score: float = Form(...),
):
    if not wav_file.filename.endswith(".wav"):
        raise HTTPException(status_code=400, detail="wav_file must be a .wav")

    wav_bytes = await wav_file.read()

    # score lyrics
    lyrics = get_song_lyrics(song_id)
    lyric_score = score_lyrics(player_transcript, lyrics)
    save_score(player_id, lyric_score, song_id)

    # Pitch scoring: compare player's sung audio against the reference song.
    # Wrapped in a broad try/except so a pitch failure never blocks the final score response.
    print(f"[main] starting pitch scoring for song_id={song_id}, player_id={player_id}", flush=True)
    try:
        # Write the player's WAV to disk; compare_pitch expects a file path
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as client_tmp:
            client_tmp.write(wav_bytes)
            client_path = client_tmp.name
        print(f"[main] client WAV written to {client_path} ({len(wav_bytes)} bytes)", flush=True)

        # Use cached reference pitches if available; otherwise fetch WAV and analyze on the fly.
        # ref_path is tracked separately so the finally block only unlinks it when we created it here.
        if song_id in _ref_pitch_cache:
            print(f"[main] using cached reference pitch windows for {song_id}", flush=True)
            ref_path = None
            ref_pitches = _ref_pitch_cache[song_id]
        else:
            ref_wav_bytes = get_song_wav(song_id)
            print(f"[main] fetched reference WAV: {len(ref_wav_bytes)} bytes (no cache — consider calling /songs/{song_id}/precompute_pitch)", flush=True)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as ref_tmp:
                ref_tmp.write(ref_wav_bytes)
                ref_path = ref_tmp.name
            ref_pitches = precompute_ref_pitches(ref_path)
            # Populate the cache so future requests for this song skip the fetch.
            _ref_pitch_cache[song_id] = ref_pitches

        try:
            pitch_results = compare_pitch(client_path, ref_pitches=ref_pitches)
            pitch_score = pitch_results["score"]
            print(f"[main] pitch scoring complete: score={pitch_score}%, windows scored={len(pitch_results['windows'])}", flush=True)
        finally:
            # Clean up both temp files regardless of whether compare_pitch succeeded.
            os.unlink(client_path)
            if ref_path:
                os.unlink(ref_path)
            print(f"[main] cleaned up temp WAV files", flush=True)
    except Exception as e:
        # Pitch scoring is best-effort; fall back to 0 so the round can still complete.
        print(f"[main] pitch scoring failed: {e!r}, defaulting pitch_score=0.0", flush=True)
        pitch_score = 0.0

    move_score = move_score if move_score is not None else 0.0

    print(f"[main] score breakdown — lyric={lyric_score} (45%), pitch={pitch_score} (10%), move={move_score} (45%)", flush=True)
    final_score = (lyric_score * 0.10) + (pitch_score * 0.45) + (move_score * 0.45)
    print(f"[main] final_score={final_score:.2f} for player_id={player_id}", flush=True)
    update_song_leaderboard(song_id, player_id, final_score)

    return {
        "final_score": final_score,
    }


@app.get("/leaderboard/{song_id}", summary="Get leaderboard for a given song", tags=["Leaderboard"])
async def get_leaderboard(song_id: str):
    leaderboard = get_song_leaderboard(song_id)
    return {
        "song_id": song_id,
        "leaderboard": leaderboard,
    }
