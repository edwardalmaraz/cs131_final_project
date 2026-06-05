import os
import subprocess
import threading
import wave

# Our test microphones
# # Wireless USB mic
# MIC_NAME = "Jieli"

# # EarPods mic
# MIC_NAME = "EarPods"

MIC_NAME = "Jieli"  
SR = 48000
CHANNELS = 1
SAMPLE_WIDTH = 2  # int16 
OUTPUT_FILE = "user-audio/output.wav"


def _find_alsa_card(name_hint):
    """Return 'plughw:N,0' for the first ALSA card whose name contains name_hint."""
    try:
        with open("/proc/asound/cards") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):

            parts = line.strip().split()
            if parts and parts[0].isdigit():

                # check both the card line and the description line below it
                block = line + (lines[i + 1] if i + 1 < len(lines) else "")

                if name_hint.lower() in block.lower():
                    return f"plughw:{parts[0]},0"
    except OSError:
        pass
    print(f"[record] mic '{name_hint}' not found — falling back to default")
    return "default"
    # little bugggy when both mics are present, just keep one for now

DEVICE = _find_alsa_card(MIC_NAME)

_proc = None
_wav_file = None
_thread = None
_active = False
_stop_evt = threading.Event()

# Continuously read audio data from the subprocess and write to the WAV file when active/
# Be careful not to let the WAV file grow indefinitely, cause docker to eat memory frast and crash
def _reader_loop():
    chunk = SR * CHANNELS * SAMPLE_WIDTH // 10  
    while not _stop_evt.is_set():
        data = _proc.stdout.read(chunk)
        if not data:
            break
        if _active and _wav_file:
            _wav_file.writeframes(data)

# Start recording from the microphone and save to a WAV file
def start_recording():
    global _proc, _wav_file, _thread, _active, _stop_evt
    os.makedirs("user-audio", exist_ok=True)
    _stop_evt = threading.Event()
    _active = True

    _wav_file = wave.open(OUTPUT_FILE, "wb")
    _wav_file.setnchannels(CHANNELS)
    _wav_file.setsampwidth(SAMPLE_WIDTH)
    _wav_file.setframerate(SR)

    _proc = subprocess.Popen(
        ["arecord", "-D", DEVICE, "-f", "S16_LE", "-r", str(SR), "-c", str(CHANNELS), "-"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    _thread = threading.Thread(target=_reader_loop, daemon=True)
    _thread.start()
    print(f"[record] started (device={DEVICE})")


def pause_recording():
    global _active
    _active = False
    print("[record] paused")


def resume_recording():
    global _active
    _active = True
    print("[record] resumed")

# Stop recording, clean up resources, and save the WAV file
def stop_recording():
    global _proc, _wav_file, _thread, _active
    _active = False
    _stop_evt.set()

    if _proc:
        _proc.terminate()
        _proc.wait()
        _proc = None

    if _thread:
        _thread.join(timeout=2)
        _thread = None

    if _wav_file:
        _wav_file.close()
        _wav_file = None
        print(f"[record] saved to {OUTPUT_FILE}")
    else:
        print("[record] nothing recorded")
