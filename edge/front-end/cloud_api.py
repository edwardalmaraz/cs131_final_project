import requests

API_BASE_URL = "https://cs131-project-495722-235582859004.us-west1.run.app"


def submit_final_score(song_id, player_id, wav_path, move_score, player_transcript=""):
    try:
        with open(wav_path, "rb") as f:
            r = requests.post(
                f"{API_BASE_URL}/score/final",
                data={
                    "song_id": str(song_id),
                    "player_id": player_id,
                    "player_transcript": player_transcript,
                    "move_score": float(move_score),
                },
                files={"wav_file": ("recording.wav", f, "audio/wav")},
                timeout=15,
            )
        r.raise_for_status()
        return r.json().get("final_score")
    except Exception as e:
        print(f"submit_final_score failed: {e}")
        return None


def fetch_leaderboard(song_id):
    try:
        r = requests.get(f"{API_BASE_URL}/leaderboard/{song_id}", timeout=5)
        r.raise_for_status()
        return r.json().get("leaderboard", [])
    except Exception as e:
        print(f"fetch_leaderboard failed: {e}")
        return []


def fetch_songs():
    try:
        r = requests.get(f"{API_BASE_URL}/songs", timeout=5)
        r.raise_for_status()
        return r.json().get("songs", [])
    except Exception as e:
        print(f"fetch_songs failed: {e}")
        return []
