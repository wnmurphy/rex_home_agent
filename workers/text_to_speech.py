from .worker_thread import WorkerThread

class TextToSpeechWorkerOrca(WorkerThread):
    """
    Listens to LLM response queue for model response chunks in text.
    Synthesize each to audio.
    Add it to the tts_audio_queue.
    """
    def __init__(self, in_q, out_q, orca, **kwargs):
        super().__init__(in_q, out_q, orca=orca, **kwargs)
        self.text_buffer = ""

    def run(self):
        print("TEXT_TO_SPEECH: Thread running...")
        # Open persistent stream here to run in worker thread instead of main thread.
        self.stream = self.orca.stream_open()
        try:
            super().run()
        finally:
            final_pcm = self.stream.flush()
            if final_pcm:
                self.out_q.put(("tts", final_pcm))
            self.stream.close()

    def process(self, llm_response_chunk):

        # Flush the speech synthesis stream if this is the end of a model's response.
        if llm_response_chunk == "END_UTTERANCE":
            final_pcm = self.stream.flush()
            if final_pcm:
                self.out_q.put(("tts", final_pcm), block=True)
            return None

        # Otherwise synthesize speech for current chunk.
        self.text_buffer += llm_response_chunk

        if len(self.text_buffer) > 40 or llm_response_chunk.endswith((".", "!", "?", ",")):
            pcm = self.stream.synthesize(self.text_buffer)
            if pcm:
                self.out_q.put(("tts", pcm))
            self.text_buffer = ""
        return None


class TextToSpeechWorkerKokoro(WorkerThread):
    """
    Listens to LLM response queue for model response chunks in text.
    Synthesize each to audio.
    Add it to the tts_audio_queue.
    """
    def __init__(self, in_q, out_q, orca, **kwargs):
        super().__init__(in_q, out_q, orca=orca, **kwargs)

    def run(self):
        print("TEXT_TO_SPEECH: Thread running...")
        # Open persistent stream here to run in worker thread instead of main thread.
        self.stream = self.orca.stream_open()
        try:
            super().run()
        finally:
            final_pcm = self.stream.flush()
            if final_pcm:
                self.out_q.put(final_pcm)
            self.stream.close()

    def process(self, llm_response_chunk):

        # Flush the speech synthesis stream if this is the end of a model's response.
        if llm_response_chunk == "END_UTTERANCE":
            final_pcm = self.stream.flush()
            if final_pcm:
                self.out_q.put(final_pcm, block=True)
            return None

        # Otherwise synthesize speech for current chunk.
        pcm = self.stream.synthesize(llm_response_chunk)
        if pcm:
            self.out_q.put(pcm, block=True)
        return None