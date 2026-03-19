import threading
import time
from queue import Queue
from random import sample

import pvcheetah
import pvcobra
import pvorca
import pvporcupine
from pvrecorder import PvRecorder
from pvspeaker import PvSpeaker

from config import Config
from workers.audio_capture import AudioCaptureWorker
from workers.llm import LLMWorker
from workers.speaker import SpeakerWorker
from workers.speech_to_text import SpeechToTextWorker
from workers.text_to_speech import TextToSpeechWorkerOrca
from workers.wake_word_detection import WakeWordDetectionWorker


def setup_environment():
    # Check for required environment variables
    if not Config.PICOVOICE_LICENSE_KEY:
        print("Warning: PICOVOICE_LICENSE_KEY required but not found in environment variables")

    # Check if Ollama is running
    try:
        import requests
        response = requests.get("http://localhost:11434")
        if response.status_code != 200:
            print("Warning: Ollama server not accessible at http://localhost:11434")
    except:
        print("Warning: Could not connect to Ollama server")


def main():

    stop_event = threading.Event()

    # Create queues for communication between threads.
    audio_capture_queue = Queue(maxsize=64)
    speech_audio_queue = Queue(maxsize=64)
    stt_text_queue = Queue(maxsize=8)
    llm_response_text_queue = Queue(maxsize=64)
    audio_playback_queue = Queue(maxsize=32)

    # Initialize engines to pass into workers.
    recorder = PvRecorder(frame_length=Config.AUDIO_FRAME_LENGTH_IN_SAMPLES)
    porcupine = pvporcupine.create(
        access_key=Config.PICOVOICE_LICENSE_KEY,
        keyword_paths=[Config.PORCUPINE_WAKE_WORD_PATH]
    )
    cobra = pvcobra.create(access_key=Config.PICOVOICE_LICENSE_KEY)
    cheetah = pvcheetah.create(
        access_key=Config.PICOVOICE_LICENSE_KEY,
        enable_automatic_punctuation=True,
        endpoint_duration_sec=Config.SECONDS_OF_SILENCE_THAT_INDICATES_USER_IS_DONE_SPEAKING,
    )
    orca = pvorca.create(
        access_key=Config.PICOVOICE_LICENSE_KEY,
        model_path=Config.TTS_MODEL_PATH,
    )
    speaker = PvSpeaker(
        sample_rate=Config.SAMPLE_RATE_OUTPUT_AUDIO,
        bits_per_sample=16,
        buffer_size_secs=Config.SPEAKER_BUFFER_SIZE_IN_SECONDS,
    )

    # Initialize workers, where each worker has its own engine and thread.
    workers = [

        # Captures audio input from microphone, and writes it to the audio capture queue.
        AudioCaptureWorker(
            in_q=None,
            out_q=audio_capture_queue,
            recorder=recorder
        ),

        # Passes audio from the capture queue to the speech queue, writing wake event if detected.
        WakeWordDetectionWorker(
            in_q=audio_capture_queue,
            out_q=speech_audio_queue,
            porcupine=porcupine,
            audio_playback_queue=audio_playback_queue,
        ),

        # Converts speech audio in the speech queue to text, and writes that text to the text queue.
        SpeechToTextWorker(
            in_q=speech_audio_queue,
            out_q=stt_text_queue,
            cheetah=cheetah
        ),

        # Sends text to the language model for processing, and writes streaming model output to the LLM response queue.
        LLMWorker(
            in_q=stt_text_queue,
            out_q=llm_response_text_queue,
            audio_playback_queue=audio_playback_queue,
        ),

        # Converts text from LLM response queue into synthesized speech, and writes speech chunks to the TTS queue.
        TextToSpeechWorkerOrca(
            in_q=llm_response_text_queue,
            out_q=audio_playback_queue,
            orca=orca
        ),

        # Plays synthesized speech from the TTS queue to the speaker as audio.
        SpeakerWorker(
            in_q=audio_playback_queue,
            out_q=None,
            speaker=speaker,
        ),
    ]

    recorder.start()
    speaker.start()

    for w in workers:
        w.start()

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        stop_event.set()

        audio_capture_queue.put(None)
        speech_audio_queue.put(None)
        stt_text_queue.put(None)
        llm_response_text_queue.put(None)
        audio_playback_queue.put(None)

        for w in workers:
            w.join()

    finally:
        recorder.stop()
        recorder.delete()
        porcupine.delete()
        cheetah.delete()
        orca.delete()
        speaker.stop()
        speaker.delete()


if __name__ == "__main__":
    setup_environment()
    main()
