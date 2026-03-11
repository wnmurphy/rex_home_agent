from .worker_thread import WorkerThread

class SpeakerWorker(WorkerThread):
    """
    Write PCMs from the tts_audio_queue to the speaker to play audio output.
    """
    def __init__(self, in_q, out_q, speaker, **kwargs):
        super().__init__(in_q, out_q, speaker=speaker, **kwargs)

    def process(self, pcm):
        print(f"SpeakerWorker received: {pcm}")
        if pcm:
            self.speaker.write(pcm)