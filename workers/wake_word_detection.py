import threading

from config import Config
from utils import load_wav_pcm

from .worker_thread import WorkerThread

class WakeWordDetectionWorker(WorkerThread):
    """
    Listens continuously to audio capture queue for wake word.
    Forwards audio PCM events continuously to speech audio queue,
    adding wake word event if detected.
    """
    def __init__(self, in_q, out_q, porcupine, audio_queue, **kwargs):
        super().__init__(in_q, out_q, porcupine=porcupine, audio_queue=audio_queue, **kwargs)
        self.wake_sound_pcm = load_wav_pcm(Config.PATH_TO_WAKE_SOUND)

    def run(self):
        print("WAKE_WORD_DETECTION: Say 'Hey Rex' to start...")
        super().run()

    def process(self, pcm):
        if self.porcupine.process(pcm) >= 0:
            print("\n[Wake Word Detected]")
            self.audio_queue.put(("wake", self.wake_sound_pcm))
            self.out_q.put(("WAKE", None))
        else:
            self.out_q.put(("PCM", pcm))
