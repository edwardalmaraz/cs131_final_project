import os
import tempfile
import wave

import librosa
import numpy as np

#helper
def get_wav_duration(wav_path):
    with wave.open(str(wav_path), "rb") as wav_file:
        return wav_file.getnframes() / wav_file.getframerate()


def analyze_pitch_windows(wav_path, window_sec=3, hop_length=512, duration=None):
    """Returns list of dominant Hz per window."""

    print(f"Analyzing {wav_path}...", flush=True)

    audio, sr = librosa.load(wav_path, sr=None, duration=duration)
    # set sampling rate as None to preserve original samples per second
    # audio is the numpy array of audio samples
    # sr sets to our .wav's original sampling rate

    f0, voiced_flag, _ = librosa.pyin(
        audio,
        fmin=float(librosa.note_to_hz("C2")),
        fmax=float(librosa.note_to_hz("C7")),
        hop_length=hop_length
    )
    # librosa pyin returns 3 things:
    # 1. fundamental frequencies (f0 array) -> this is already compressed
    #    However, we need to compress more. Its hop length is 512 samples by default
    # 2. voice_flag: was a pitch sung (also an array)
    # 3. confidence probability of previous array predictions (we don't use this)

    frames_per_window = int(window_sec * sr / hop_length)
    # divide by hop_length because pyin doesn't give you 1 f0 value per sample.
    dominant_frequencies = []

    for i in range(0, len(f0), frames_per_window):

        window = f0[i:i + frames_per_window]  # current window
        voiced = window[~np.isnan(window)]    # Ignore NaN where a pitch is not detected

        if len(voiced) > 0:
            rounded = np.round(voiced)
            values, counts = np.unique(rounded, return_counts=True)
            dominant = values[np.argmax(counts)]
            dominant_frequencies.append(dominant)
        # if there was at least one marked freq

        else:
            dominant_frequencies.append(None)  # ignore this window, mark as None
        # if no frequencies

    return dominant_frequencies


def compare_pitch(client_wav, reference_wav, window_sec=3, tolerance_semitones=2, max_penalty_semitones=6):

    # parse both wav files
    client_duration = get_wav_duration(client_wav)
    client_pitches = analyze_pitch_windows(client_wav, window_sec)
    ref_pitches = analyze_pitch_windows(reference_wav, window_sec, duration=client_duration)

    # Compare only windows where both have detected pitch
    matched = 0
    compared = 0
    results = []

    for i, (client_hz, ref_hz) in enumerate(zip(client_pitches, ref_pitches)):
        if client_hz is None or ref_hz is None:
            continue  # don't score silent windows

        # Convert Hz difference to semitones

        # semitones = 12 * log2(f1/f2)
        raw_semitone_diff = abs(12 * np.log2(client_hz / ref_hz))

        # Treat the same note in a different octave as close.
        pitch_class_diff = raw_semitone_diff % 12
        semitone_diff = min(pitch_class_diff, 12 - pitch_class_diff)

        if semitone_diff <= tolerance_semitones:
            window_score = 1.0
        else:
            penalty_range = max_penalty_semitones - tolerance_semitones
            if penalty_range <= 0:
                penalty_range = 1
            window_score = 1 - ((semitone_diff - tolerance_semitones) / penalty_range)
            window_score = max(0, window_score)

        is_close = semitone_diff <= tolerance_semitones
        if is_close:
            matched += 1
        compared += 1

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

    total_window_score = sum(window["window_score"] for window in results)
    score = (total_window_score / compared) if compared > 0 else 0

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
    pitch_results = compare_pitch("output.wav", "cupid-vocals.wav")
    print_pitch_results(pitch_results)