from array import array

from config import Config
from .worker_thread import WorkerThread

class SpeakerWorker(WorkerThread):
    """
    Write PCMs from the tts_audio_queue to the speaker to play audio output.

    Buffers because Orca produces variable-rate
    """
    def __init__(self, in_q, out_q, speaker, **kwargs):
        super().__init__(in_q, out_q, speaker=speaker, **kwargs)
        self.buffer = array("h")

    def process(self, pcm):
        frame_length = Config.AUDIO_FRAME_LENGTH_IN_SAMPLES

        if not pcm:
            return None

        # Orca TTS produces variable-size PCMs. Buffer and re-chunk here...
        self.buffer.extend(pcm)
        while len(self.buffer) >= frame_length:
            frame = self.buffer[:frame_length]
            self.buffer = self.buffer[frame_length:]
            self.speaker.write(frame)
