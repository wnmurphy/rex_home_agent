import queue
import threading
import time
import wave
import yaml

from array import array

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from config import Config

def load_wav_pcm(wav_path):
    with wave.open(wav_path, "rb") as wf:
        assert wf.getsampwidth() == 2, "Expected 16-bit PCM"
        assert wf.getnchannels() == 1, "Expected mono audio"
        frames = wf.readframes(wf.getnframes())
        return array("h", frames)


def thinking_sound_loop(stop_event, audio_playback_queue, wav_pcm):
    while not stop_event.is_set():
        try:
            audio_playback_queue.put(("thinking_in_progress", wav_pcm), timeout=0.05)
        except queue.Full:
            pass


# Loads a YAML file into a dictionary.
def load_prompt(prompt_key):
    with open(f"./prompts/{prompt_key}.yaml", "r") as f:
        return yaml.safe_load(f)


def convert_message_list_to_string(message_list):
    type_to_string_map = {
        AIMessage: "assistant",
        HumanMessage: "user",
        SystemMessage: "system",
    }
    context_messages = [
        f"{type_to_string_map[type(m)]}: {m.content}"
        for m in message_list
        if getattr(m, "content", None) and not isinstance(m, ToolMessage)
    ]
    return "\n\n".join(context_messages)
