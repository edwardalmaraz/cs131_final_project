import wave
from concurrent.futures import ThreadPoolExecutor

import librosa
import numpy as np
from numba import njit, prange

_ANALYSIS_SR = 16000
_HOP_LENGTH = 2048


def get_wav_duration(wav_path):
    with wave.open(str(wav_path), "rb") as wav_file:
        return wav_file.getnframes() / wav_file.getframerate()


@njit(parallel=True)
def _find_dominant_windows(f0, frames_per_window):
    """For each window, return the most common voiced Hz, or NaN if silent."""
    n_windows = (len(f0) + frames_per_window - 1) // frames_per_window
    dominant = np.full(n_windows, np.nan)

    for w in prange(n_windows):
        start = w * frames_per_window
        end = min(start + frames_per_window, len(f0))

        voiced_count = 0
        for i in range(start, end):
            if not np.isnan(f0[i]):
                voiced_count += 1

        if voiced_count == 0:
            continue

        voiced = np.empty(voiced_count)
        j = 0
        for i in range(start, end):
            if not np.isnan(f0[i]):
                voiced[j] = round(f0[i])
                j += 1

        # Find mode (O(n^2) is fine — windows are ~23 frames at most)
        best_val = voiced[0]
        best_count = 0
        for i in range(voiced_count):
            c = 0
            for k in range(voiced_count):
                if voiced[k] == voiced[i]:
                    c += 1
            if c > best_count:
                best_count = c
                best_val = voiced[i]

        dominant[w] = best_val

    return dominant


# Warm up the JIT at import time so the first request doesn't pay compilation cost
_find_dominant_windows(np.array([440.0, np.nan, 220.0], dtype=np.float64), 2)


def analyze_pitch_windows(wav_path, window_sec=3, duration=None):
    """Returns list of dominant Hz per window (or None for silent windows)."""

    print(f"[pitch] analyze_pitch_windows: loading {wav_path} (duration limit={duration})", flush=True)

    audio, sr = librosa.load(wav_path, sr=_ANALYSIS_SR, duration=duration)

    print(f"[pitch] loaded audio: sr={sr} Hz, samples={len(audio)}, actual duration={len(audio)/sr:.2f}s", flush=True)

    f0, voiced_flag, _ = librosa.pyin(
        audio,
        fmin=float(librosa.note_to_hz("C2")),
        fmax=float(librosa.note_to_hz("C7")),
        hop_length=_HOP_LENGTH,
        sr=sr,
    )

    frames_per_window = max(1, int(window_sec * sr / _HOP_LENGTH))
    voiced_frame_count = int(np.sum(~np.isnan(f0)))
    print(f"[pitch] pyin: {len(f0)} f0 frames, {voiced_frame_count} voiced", flush=True)

    dominant_raw = _find_dominant_windows(f0, frames_per_window)
    dominant_frequencies = [None if np.isnan(v) else float(v) for v in dominant_raw]

    print(f"[pitch] analyze_pitch_windows done: {len(dominant_frequencies)} windows total", flush=True)
    return dominant_frequencies


def precompute_ref_pitches(ref_wav_path, window_sec=3):
    """Analyze a reference WAV once and return the window list for caching."""
    print(f"[pitch] precomputing reference pitches for {ref_wav_path}", flush=True)
    return analyze_pitch_windows(ref_wav_path, window_sec=window_sec)


def compare_pitch(client_wav, reference_wav=None, ref_pitches=None, window_sec=3, tolerance_semitones=2, max_penalty_semitones=6):
    """
    Compare client pitch against reference.
    Pass ref_pitches (precomputed list) to skip reference analysis entirely.
    Pass reference_wav to analyze client and reference in parallel threads.
    """

    print(f"[pitch] compare_pitch: client={client_wav}", flush=True)
    print(f"[pitch] params: window_sec={window_sec}, tolerance={tolerance_semitones} semitones, max_penalty={max_penalty_semitones} semitones", flush=True)

    client_duration = get_wav_duration(client_wav)
    print(f"[pitch] client duration: {client_duration:.2f}s", flush=True)

    if ref_pitches is not None:
        # Reference already cached — only analyze client
        client_pitches = analyze_pitch_windows(client_wav, window_sec)
        ref_pitches = ref_pitches[:len(client_pitches)]
        print(f"[pitch] using cached reference pitches ({len(ref_pitches)} windows)", flush=True)
    elif reference_wav is not None:
        # Run client and reference pyin concurrently (pyin releases the GIL)
        print(f"[pitch] running client + reference analysis in parallel", flush=True)
        with ThreadPoolExecutor(max_workers=2) as pool:
            f_client = pool.submit(analyze_pitch_windows, client_wav, window_sec)
            f_ref = pool.submit(analyze_pitch_windows, reference_wav, window_sec, client_duration)
            client_pitches = f_client.result()
            ref_pitches = f_ref.result()
    else:
        raise ValueError("Either reference_wav or ref_pitches must be provided")

    print(f"[pitch] client windows: {len(client_pitches)}, ref windows: {len(ref_pitches)}", flush=True)

    matched = 0
    compared = 0
    skipped = 0
    results = []

    for i, (client_hz, ref_hz) in enumerate(zip(client_pitches, ref_pitches)):
        if client_hz is None or ref_hz is None:
            skipped += 1
            continue

        raw_semitone_diff = abs(12 * np.log2(client_hz / ref_hz))
        pitch_class_diff = raw_semitone_diff % 12
        semitone_diff = min(pitch_class_diff, 12 - pitch_class_diff)

        if semitone_diff <= tolerance_semitones:
            window_score = 1.0
        else:
            penalty_range = max_penalty_semitones - tolerance_semitones
            if penalty_range <= 0:
                penalty_range = 1
            window_score = max(0.0, 1 - ((semitone_diff - tolerance_semitones) / penalty_range))

        is_close = semitone_diff <= tolerance_semitones
        if is_close:
            matched += 1
        compared += 1

        print(
            f"[pitch]   window {i} ({i * window_sec}s): "
            f"client={librosa.hz_to_note(client_hz)}({client_hz:.1f} Hz) "
            f"ref={librosa.hz_to_note(ref_hz)}({ref_hz:.1f} Hz) "
            f"diff={semitone_diff:.2f}st score={round(window_score * 100, 1)}% {'MATCH' if is_close else 'miss'}",
            flush=True
        )

        results.append({
            "window": i,
            "time_sec": i * window_sec,
            "client_hz": round(client_hz, 1),
            "client_note": librosa.hz_to_note(client_hz),
            "ref_hz": round(ref_hz, 1),
            "ref_note": librosa.hz_to_note(ref_hz),
            "semitones_off": round(semitone_diff, 2),
            "raw_semitones_off": round(raw_semitone_diff, 2),
            "window_score": round(window_score * 100, 1),
            "match": is_close
        })

    total_window_score = sum(w["window_score"] for w in results)
    score = (total_window_score / compared) if compared > 0 else 0

    print(f"[pitch] compare_pitch done: {compared} scored, {matched} matched, {skipped} skipped => score={round(score, 1)}%", flush=True)

    return {
        "score": round(score, 1),
        "windows": results
    }


def print_pitch_results(results):
    print("\nPitch Score")
    print(f"Score: {results['score']}%")
    print("Results:")

    if len(results["windows"]) == 0:
        print("No voiced windows were found to compare.")
        return

    for window in results["windows"]:
        if window["match"]:
            match_text = "match"
        elif window["window_score"] > 0:
            match_text = "partial"
        else:
            match_text = "miss"

        print(
            f"{window['time_sec']:>4}s | "
            f"user {window['client_note']} ({window['client_hz']} Hz) | "
            f"ref {window['ref_note']} ({window['ref_hz']} Hz) | "
            f"{window['semitones_off']} semitones off, octave adjusted | "
            f"{window['window_score']}% | "
            f"{match_text}"
        )


if __name__ == "__main__":
    pitch_results = compare_pitch("output.wav", reference_wav="cupid-vocals.wav")
    print_pitch_results(pitch_results)
