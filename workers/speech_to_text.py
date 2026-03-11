from .worker_thread import WorkerThread

class SpeechToTextWorker(WorkerThread):
    """
    Listens continuously to speech audio queue.
    When wake word event is seen,
    - clears text buffer,
    - transcribes speech to text, and
    - forwards the result to text queue
    """
    def __init__(self, in_q, out_q, cheetah, **kwargs):
        super().__init__(in_q, out_q, cheetah=cheetah, **kwargs)
        self.buffer = []
        self.is_recording = False

    def run(self):
        print("SPEECH_TO_TEXT: Thread running...")
        super().run()

    def process(self, item):
        # print(f"SpeechToTextWorker received: {item}")

        item_type, data = item

        if item_type == "WAKE":
            self.is_recording = True
            self.buffer = []
            return None

        if item_type == "PCM" and self.is_recording:
            text, endpoint = self.cheetah.process(data)

            if text:
                self.buffer.append(text)

            if endpoint:
                final = self.cheetah.flush()
                if final:
                    self.buffer.append(final)

                self.is_recording = False

                return "".join(self.buffer)

        return None