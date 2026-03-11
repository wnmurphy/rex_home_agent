from .worker_thread import WorkerThread

class AudioCaptureWorker(WorkerThread):
    """
    Listens continuously to the microphone device,
    Writes PCMs continuously to the audio capture queue.
    """
    def __init__(self, in_q, out_q, recorder, **kwargs):
        super().__init__(in_q, out_q, recorder=recorder, **kwargs)

    def run(self):
        self.recorder.start()
        print("AUDIO_CAPTURE: Recorder active.")

        # Listen indefinitely unless the thread is terminated.
        while not self.stop_event.is_set():
            pcm = self.recorder.read()

            if self.out_q:
                self.out_q.put(pcm, timeout=0.1)

        self.recorder.stop()
