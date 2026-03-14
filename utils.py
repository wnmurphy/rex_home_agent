import random
import time
import wave
import yaml

from array import array

from config import Config

def load_wav_pcm(wav_path):
    with wave.open(wav_path, "rb") as wf:
        assert wf.getsampwidth() == 2, "Expected 16-bit PCM"
        assert wf.getnchannels() == 1, "Expected mono audio"
        frames = wf.readframes(wf.getnframes())
        return array("h", frames)

def thinking_sound_loop(stop_event, audio_queue, wav_pcm):
    while not stop_event.is_set():
        audio_queue.put(("thinking", wav_pcm))
        random_sleep = random.uniform(0.8, 1.2)
        time.sleep(random_sleep)

# Loads a YAML file into a dictionary.
def load_prompt(prompt_path):
    with open(prompt_path, "r") as f:
        return yaml.safe_load(f)
