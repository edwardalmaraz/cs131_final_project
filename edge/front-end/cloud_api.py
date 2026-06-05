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
                timeout=None,
            )
        if not r.ok:
            print(f"submit_final_score failed: {r.status_code} — {r.text}")
            return None
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


def download_song(song_id):
    """Download metadata.json and audio.mp3 for a song into the songs/ directory.
    Backs up the originals as .default files so they can be restored on exit."""
    import os, json, shutil
    os.makedirs("songs", exist_ok=True)
    for fname in ["songs/metadata.json", "songs/audio.mp3"]:
        if os.path.exists(fname) and not os.path.exists(fname + ".default"):
            shutil.copy2(fname, fname + ".default")
    try:
        r = requests.get(f"{API_BASE_URL}/songs/{song_id}/meta_data", timeout=10)
        r.raise_for_status()
        with open("songs/metadata.json", "w") as f:
            json.dump(r.json(), f)
    except Exception as e:
        print(f"download_song metadata failed: {e}")
        return False
    try:
        r = requests.get(f"{API_BASE_URL}/songs/{song_id}/mp3", timeout=30)
        r.raise_for_status()
        with open("songs/audio.mp3", "wb") as f:
            f.write(r.content)
    except Exception as e:
        print(f"download_song audio failed: {e}")
        return False
    return True
