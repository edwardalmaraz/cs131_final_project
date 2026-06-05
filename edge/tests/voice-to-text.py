from faster_whisper import WhisperModel


# Load the model (CPU mode for easiest setup on Jetson Nano)
model = WhisperModel("tiny.en", device="cuda", compute_type="int8")



# Recording settings
duration = 10          # seconds to record
sample_rate = 16000   # Whisper works well at 16 kHz


# print("Recording...")
# audio = sd.rec(
#    int(duration * sample_rate),
#    samplerate=sample_rate,
#    channels=1,
#    dtype="int16"
# )
# sd.wait()
# print("Recording complete.")


# # Save to a temporary WAV file
# write("mic_input.wav", sample_rate, audio)


# Transcribe the recorded audio
segments, info = model.transcribe("../front-end/user-audio/output.wav")


print("\nTranscription:")
for segment in segments:
   print(segment.text)





