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
        self.tts_active = False

    def process(self, item):
        frame_length = Config.AUDIO_FRAME_LENGTH_IN_SAMPLES

        if not item:
            return

        tag, pcm = item

        if tag == "clear_thinking":
            self.buffer.clear()
            return

        if tag in ["wake", "thinking"]:
            if not self.tts_active:
                self.speaker.write(pcm)
            return

        if tag == "tts":
            self.tts_active = True
            # Orca TTS produces variable-size PCMs. Buffer and re-chunk here...
            self.buffer.extend(pcm)
            while len(self.buffer) >= frame_length:
                frame = self.buffer[:frame_length]
                self.buffer = self.buffer[frame_length:]
                self.speaker.write(frame)
