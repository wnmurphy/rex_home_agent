import random
import time
import wave
import yaml

from array import array

from config import Config


def play_wav(speaker, wav_path):
    # Resample any sound you use to 22k Hz:
    # ffmpeg -i thinking_sound.wav -ar 22050 -ac 1 -sample_fmt s16 thinking_sound_pcm.wav
    with wave.open(wav_path, "rb") as wf:
        assert wf.getsampwidth() == 2, "Expected 16-bit PCM"
        assert wf.getnchannels() == 1, "Expected mono audio"
        frames = wf.readframes(wf.getnframes())
        pcm = array("h", frames)
        frame_length = Config.AUDIO_FRAME_LENGTH_IN_SAMPLES
        for i in range(0, len(pcm), frame_length):
            speaker.write(pcm[i:i+frame_length])

def thinking_sound_loop(stop_event, speaker):
    while not stop_event.is_set():
        play_wav(speaker, Config.PATH_TO_THINKING_SOUND)
        random_sleep = random.uniform(0.8, 1.2)
        time.sleep(random_sleep)

# Loads a YAML file into a dictionary.
def load_prompt(prompt_path):
    with open(prompt_path, "r") as f:
        return yaml.safe_load(f)
