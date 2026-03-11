from .worker_thread import WorkerThread

class WakeWordDetectionWorker(WorkerThread):
    """
    Listens continuously to audio capture queue for wake word.
    Forwards audio PCM events continuously to speech audio queue,
    adding wake word event if detected.
    """
    def __init__(self, in_q, out_q, porcupine, **kwargs):
        super().__init__(in_q, out_q, porcupine=porcupine, **kwargs)

    def run(self):
        print("WAKE_WORD_DETECTION: Say 'Hey Rex' to start...")
        super().run()

    def process(self, pcm):
        # print(f"WakeWordDetectionWorker got: {pcm}")
        if self.porcupine.process(pcm) >= 0:
            print("\n[Wake Word Detected] How can I help?")
            self.out_q.put(("WAKE", None))
        else:
            self.out_q.put(("PCM", pcm))
