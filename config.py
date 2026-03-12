import os
from pathlib import Path


class Config:

    # Picovoice
    PICOVOICE_LICENSE_KEY = os.getenv("PICOVOICE_LICENSE_KEY")

    # Audio settings
    SAMPLE_RATE_INPUT_AUDIO = 16000
    SAMPLE_RATE_OUTPUT_AUDIO = 22050
    AUDIO_FRAME_LENGTH_IN_SAMPLES = 512
    SPEAKER_BUFFER_SIZE_IN_SECONDS = 300

    # VAD settings
    VOICE_DETECTION_THRESHOLD = 0.2 # probability of voice activity required to trigger assistant.

    SECONDS_OF_SILENCE_THAT_INDICATES_USER_IS_DONE_SPEAKING = 3.0

    # Wake word settings
    PORCUPINE_WAKE_WORD_PATH = "./models/Hey-Rex_en_mac_v4_0_0.ppn"

    # STT settings
    WHISPER_MODEL = "base"

    # Ollama settings
    OLLAMA_HOST = "http://localhost:11434"
    OLLAMA_MODEL = "huihui_ai/mistral-small-abliterated:latest"

    # TTS settings
    TTS_MODEL_PATH = "./models/orca_params_en_female.pv"

    # Sounds
    PATH_TO_WAKE_SOUND = "./sounds/wake_sound_pcm.wav"
    PATH_TO_THINKING_SOUND = "./sounds/thinking_sound_pcm.wav"

    # Prompts
    SYSTEM_PROMPT_PATH = "./prompts/system_prompt.yaml"
