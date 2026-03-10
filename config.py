import os
from pathlib import Path


class Config:

    # Picovoice
    PICOVOICE_LICENSE_KEY = os.getenv("PICOVOICE_LICENSE_KEY")

    # Audio settings
    SAMPLE_RATE = 16000
    CHUNK_SIZE = 1024
    BUFFER_SIZE = 4096

    # VAD settings
    VOICE_DETECTION_THRESHOLD = 0.5 # probability of voice activity required to trigger assistant.

    SECONDS_OF_SILENCE_BEFORE_SUBMITTING_TO_OLLAMA = 1.0

    # Wake word settings
    WAKE_WORD = "hey rex"
    PORCUPINE_MODEL_PATH = "models/porcupine_params.ppn"
    PORCUPINE_WAKE_WORD_PATH = "models/porcupine_wake_word.ppn"

    # STT settings
    WHISPER_MODEL = "base"
    MIN_RECORDED_FRAMES = 100
    SAMPLE_RATE = 16000

    # Ollama settings
    OLLAMA_HOST = "http://localhost:11434"
    OLLAMA_MODEL = "huihui_ai/mistral-small-abliterated:latest"

    # TTS settings
    TTS_MODEL = "orca"  # or "sherpa-onnx"
    TTS_SAMPLE_RATE = 22050
