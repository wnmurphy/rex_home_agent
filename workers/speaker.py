from array import array
from queue import Empty

from config import Config
from .worker_thread import WorkerThread

class SpeakerWorker(WorkerThread):
    """
    Write PCMs from the audio_playback_queue to the speaker to play audio output.

    Buffers because Orca produces variable-rate
    """
    def __init__(self, in_q, out_q, speaker, **kwargs):
        super().__init__(in_q, out_q, speaker=speaker, **kwargs)
        self.buffer = array("h")
        self.is_tts_playing = False
        self.is_sound_effect_playing = False

    def process(self, item):
        frame_length = Config.AUDIO_FRAME_LENGTH_IN_SAMPLES

        if not item:
            return

        tag, pcm = item

        # print(f"Speaker worker got: {tag}")

        if tag == "clear_thinking":
            self.buffer.clear()
            return

        if tag in ["wake", "thinking"]:
            if not self.is_sound_effect_playing:
                self.is_sound_effect_playing = True
                self.speaker.write(pcm)
                self.is_sound_effect_playing = False
            return

        if tag == "tts":
            # NOTE: About 8s between when we start receiving TTS PCMs here and when we actually hear the speech.
            self.is_tts_playing = True
            self.speaker.write(pcm)
