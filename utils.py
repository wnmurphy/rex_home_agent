import wave
from array import array

def play_wav(speaker, wav_path):
    with wave.open(wav_path, "rb") as wf:
        assert wf.getsampwidth() == 2, "Expected 16-bit PCM"
        assert wf.getnchannels() == 1, "Expected mono audio"
        frame_rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
        pcm = array("h", frames)
        frame_length = 512  # match your Config.AUDIO_FRAME_LENGTH_IN_SAMPLES
        for i in range(0, len(pcm), frame_length):
            speaker.write(pcm[i:i+frame_length])