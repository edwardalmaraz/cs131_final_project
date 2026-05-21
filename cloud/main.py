from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from database import *
from pydantic import BaseModel
from scoring.text import score_lyrics
from typing import Optional
import io
import base64

app = FastAPI()
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
    title: str = Form(...),
    artist: str = Form(...),
    album: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    genre: Optional[str] = Form(None),
    bpm: Optional[int] = Form(None),
    mp3_file: UploadFile = File(...),
    lyrics_file: UploadFile = File(...),
):
    if not mp3_file.filename.endswith(".mp3"):
        raise HTTPException(status_code=400, detail="mp3_file must be a .mp3")

    mp3_bytes = await mp3_file.read()
    lyrics_text = None
    if lyrics_file is not None:
        lyrics_bytes = await lyrics_file.read()
        lyrics_text = lyrics_bytes.decode("utf-8")

    metadata = upload_song(
        song_id=song_id,
        title=title,
        artist=artist,
        mp3_bytes=mp3_bytes,
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

    # TODO: pitch scoring
    pitch_score = 0.0

    # TODO: moves scoring
    # move_score is currently passed from the Jetson client, but if not available it should be computed separately.
    move_score = move_score if move_score is not None else 0.0

    final_score = (lyric_score * 0.45) + (pitch_score * 0.10) + (move_score * 0.45)
    update_song_leaderboard(song_id, player_id, final_score)

    return {
        "player_id": player_id,
        "song_id": song_id,
        "lyric_score": lyric_score,
        "pitch_score": pitch_score,
        "move_score": move_score,
        "final_score": final_score,
    }


@app.get("/leaderboard/{song_id}", summary="Get leaderboard for a given song", tags=["Leaderboard"])
async def get_leaderboard(song_id: str):
    leaderboard = get_song_leaderboard(song_id)
    return {
        "song_id": song_id,
        "leaderboard": leaderboard,
    }
