import sounddevice as sd
import scipy.io.wavfile as wav
import numpy as np

sr = 44100 # frames per second
seconds = 5

def record(filename="user-audio/output.wav"):
    audio = sd.rec(int(seconds * sr), samplerate=sr, channels=1, dtype=np.int16)
    print(f"Started Recording")
    sd.wait()
    wav.write(filename, sr, audio)
    print(f"Saved to {filename}")

if __name__ == "__main__":
    record()