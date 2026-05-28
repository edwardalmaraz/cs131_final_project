from google.cloud import storage
import re
import json
import time
from typing import Optional

client = storage.Client()
song_bucket = client.bucket("cs131_song_bucket")
leaderboard_bucket = client.bucket("cs131_leaderboard_bucket")


def normalize(text: str):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_song_lyrics(song_id: str) -> str:
    blob = song_bucket.blob(f"{song_id}/lyrics.txt")
    raw = blob.download_as_text()
    return normalize(raw)


def get_song_lyrics_raw(song_id: str) -> str:
    blob = song_bucket.blob(f"{song_id}/lyrics.txt")
    return blob.download_as_text()


def get_song_metadata(song_id: str) -> dict:
    blob = song_bucket.blob(f"{song_id}/metadata.json")
    raw = blob.download_as_text()
    return json.loads(raw)


def get_song_mp3(song_id: str) -> bytes:
    blob = song_bucket.blob(f"{song_id}/audio.mp3")
    return blob.download_as_bytes()


def get_song_wav(song_id: str) -> bytes:
    blob = song_bucket.blob(f"{song_id}/vocals.wav")
    return blob.download_as_bytes()


def upload_song(
    song_id: str,
    song_title: str,
    artist_name: str,
    mp3_bytes: bytes,
    sequence_order: str,
    poses: list,
    lyrics: Optional[list] = None,
    album: Optional[str] = None,
    year: Optional[int] = None,
    genre: Optional[str] = None,
    bpm: Optional[int] = None,
) -> dict:
    metadata = {
        "song_id": song_id,
        "song_title": song_title,
        "artist_name": artist_name,
        "album": album,
        "year": year,
        "genre": genre,
        "bpm": bpm,
        "uploaded_at": int(time.time()),
        "sequence_order": sequence_order,
        "poses": poses,
    }

    song_bucket.blob(f"{song_id}/audio.mp3").upload_from_string(
        mp3_bytes, content_type="audio/mpeg"
    )
    song_bucket.blob(f"{song_id}/metadata.json").upload_from_string(
        json.dumps(metadata), content_type="application/json"
    )
    if lyrics:
        song_bucket.blob(f"{song_id}/lyrics.txt").upload_from_string(
            lyrics, content_type="text/plain"
        )

    return metadata


def list_songs() -> list:
    blobs = song_bucket.list_blobs()
    songs = []
    for blob in blobs:
        if blob.name.endswith("/metadata.json"):
            metadata = json.loads(blob.download_as_text())
            songs.append({
                "song_id": metadata["song_id"],
                "song_title": metadata["song_title"],
                "artist_name": metadata["artist_name"],
            })
    return sorted(songs, key=lambda s: s["song_title"])


def save_score(player_id: str, score: float, song_id: str):
    entry = {
        "player_id": player_id,
        "song_id": song_id,
        "score": score,
        "timestamp": int(time.time()),
    }
    blob_name = f"{song_id}/{player_id}_{entry['timestamp']}.json"
    blob = leaderboard_bucket.blob(blob_name)
    blob.upload_from_string(json.dumps(entry), content_type="application/json")


def update_song_metadata(song_id: str, updates: dict) -> dict:
    blob = song_bucket.blob(f"{song_id}/metadata.json")
    if not blob.exists():
        raise FileNotFoundError(f"Song '{song_id}' not found")
    metadata = json.loads(blob.download_as_text())
    metadata.update({k: v for k, v in updates.items() if v is not None})
    blob.upload_from_string(json.dumps(metadata, indent=2), content_type="application/json")
    return metadata


def get_song_leaderboard(song_id: str) -> list:
    blob = leaderboard_bucket.blob(f"{song_id}/leaderboard.json")
    if not blob.exists():
        return []

    raw = blob.download_as_text()
    payload = json.loads(raw)
    leaderboard = payload.get("leaderboard", [])
    if not isinstance(leaderboard, list):
        return []

    return sorted(leaderboard, key=lambda item: item.get("score", 0), reverse=True)


def update_song_leaderboard(song_id: str, player_id: str, score: float) -> list:
    blob = leaderboard_bucket.blob(f"{song_id}/leaderboard.json")
    leaderboard = []
    if blob.exists():
        raw = blob.download_as_text()
        payload = json.loads(raw)
        leaderboard = payload.get("leaderboard", [])
        if not isinstance(leaderboard, list):
            leaderboard = []

    existing = None
    for entry in leaderboard:
        if entry.get("player_id") == player_id:
            existing = entry
            break

    if existing is None:
        leaderboard.append({"player_id": player_id, "score": score})
    elif score > existing.get("score", 0):
        existing["score"] = score

    leaderboard = sorted(leaderboard, key=lambda item: item.get("score", 0), reverse=True)
    blob.upload_from_string(
        json.dumps({"song_id": song_id, "leaderboard": leaderboard}, indent=2),
        content_type="application/json",
    )
    return leaderboard