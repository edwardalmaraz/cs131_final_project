import io
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Minimal valid WAV header bytes
def make_wav_bytes() -> bytes:
    import struct
    data = b"\x00" * 44  # silence
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + len(data), b"WAVE",
        b"fmt ", 16, 1, 1, 16000, 32000, 2, 16,
        b"data", len(data),
    )
    return header + data


MOCK_LYRICS = "never gonna give you up never gonna let you down"
MOCK_LYRIC_SCORE = 0.85
MOCK_MOVE_SCORE = 0.90


@pytest.fixture(autouse=True)
def mock_db_and_scoring():
    with (
        patch("main.get_song_lyrics", return_value=MOCK_LYRICS),
        patch("main.score_lyrics", return_value=MOCK_LYRIC_SCORE),
        patch("main.save_score"),
        patch("main.update_song_leaderboard"),
    ):
        yield


def post_final(song_id="song1", player_id="player1", transcript="never gonna give you up", move_score=MOCK_MOVE_SCORE, filename="recording.wav", wav_bytes=None):
    if wav_bytes is None:
        wav_bytes = make_wav_bytes()
    return client.post(
        "/score/final",
        data={
            "song_id": song_id,
            "player_id": player_id,
            "player_transcript": transcript,
            "move_score": str(move_score),
        },
        files={"wav_file": (filename, io.BytesIO(wav_bytes), "audio/wav")},
    )


def test_returns_200_with_correct_fields():
    r = post_final()
    assert r.status_code == 200
    body = r.json()
    assert "final_score" in body


def test_final_score_formula():
    r = post_final()
    body = r.json()
    expected = (MOCK_LYRIC_SCORE * 0.45) + (0.0 * 0.10) + (MOCK_MOVE_SCORE * 0.45)
    assert abs(body["final_score"] - expected) < 1e-6




def test_rejects_non_wav_file():
    r = post_final(filename="recording.mp3")
    assert r.status_code == 400
    assert "wav" in r.json()["detail"].lower()
