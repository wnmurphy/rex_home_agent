import threading
import time

from config import Config
from utils import load_wav_pcm
from .worker_thread import WorkerThread

class SpeakerWorker(WorkerThread):
    """
    Write PCMs from the audio_playback_queue to the speaker to play audio output.
    """
    def __init__(self, in_q, out_q, speaker, **kwargs):
        super().__init__(in_q, out_q, speaker=speaker, **kwargs)
        self.is_tts_playing = False
        self.is_thinking = False
        self.is_wake_sound_playing = False
        self.thinking_sound_pcm = load_wav_pcm(Config.PATH_TO_THINKING_SOUND)

    def _play_thinking(self):
        frame_len = Config.AUDIO_FRAME_LENGTH_IN_SAMPLES
        sr = Config.SAMPLE_RATE_OUTPUT_AUDIO
        frame_duration = frame_len / sr

        while self.is_thinking:
            for i in range(0, len(self.thinking_sound_pcm), frame_len):
                if not self.is_thinking:
                    return

                t0 = time.perf_counter()
                self.speaker.write(self.thinking_sound_pcm[i:i+frame_len])

                sleep = frame_duration - (time.perf_counter() - t0)
                if sleep > 0:
                    time.sleep(sleep)

    def process(self, item):

        if not item:
            return

        tag, pcm = item

        print(f"Speaker worker got: {tag}")

        if tag == "wake":
            if not self.is_wake_sound_playing:
                self.is_wake_sound_playing = True
                self.speaker.write(pcm)
                self.is_wake_sound_playing = False
            return

        if tag == "start_thinking":
            if not self.is_thinking:
                self.is_thinking = True
                threading.Thread(target=self._play_thinking, daemon=True).start()
            return

        if tag == "thinking_in_progress":
            frame_length = Config.AUDIO_FRAME_LENGTH_IN_SAMPLES
            sample_rate = Config.SAMPLE_RATE_OUTPUT_AUDIO
            frame_duration = frame_length / sample_rate

            for i in range(0, len(pcm), frame_length):
                if not self.is_thinking:
                    break

                frame = pcm[i:i+frame_length]
                t0 = time.perf_counter()

                self.speaker.write(frame)

                elapsed = time.perf_counter() - t0
                sleep = frame_duration - elapsed
                if sleep > 0:
                    time.sleep(sleep)
            return

        if tag == "done_thinking":
            self.is_thinking = False
            return

        if tag == "tts":
            # NOTE: About 8s between when we start receiving TTS PCMs here and when we actually hear the speech.
            self.is_tts_playing = True
            self.speaker.write(pcm)
