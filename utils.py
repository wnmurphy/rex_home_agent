import threading
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

def thinking_sound_loop(stop_event, audio_playback_queue, wav_pcm):
    i = 0
    while not stop_event.is_set():
        # Play in frame-sized chunks to enable thinking sound to be interrupted.
        frame = wav_pcm[i:i+Config.AUDIO_FRAME_LENGTH_IN_SAMPLES]
        if not frame:
            i = 0
            continue
        audio_playback_queue.put(("thinking", frame))
        i += Config.AUDIO_FRAME_LENGTH_IN_SAMPLES
        threading.Event().wait(0.01)

# Loads a YAML file into a dictionary.
def load_prompt(prompt_path):
    with open(prompt_path, "r") as f:
        return yaml.safe_load(f)
