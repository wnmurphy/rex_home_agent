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
    i = 0
    frame_length = Config.AUDIO_FRAME_LENGTH_IN_SAMPLES
    frame_duration = frame_length / Config.SAMPLE_RATE_OUTPUT_AUDIO

    while not stop_event.is_set():
        if audio_playback_queue.qsize() < 2:

            # Play in frame-sized chunks to enable thinking sound to be interrupted.
            frame = wav_pcm[i:i+frame_length]
            if not frame:
                i = 0
                continue

            audio_playback_queue.put(("thinking", frame))
            i += frame_length

        time.sleep(frame_duration)


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
