import threading
import ollama

from config import Config
from utils import load_prompt, thinking_sound_loop
from .worker_thread import WorkerThread

class LLMWorker(WorkerThread):
    """
    Listens to text queue for user inputs,
    Submits them to ollama model,
    Writes chunks of streaming response from ollama model to the llm response queue.
    """
    def __init__(self, in_q, out_q, speaker, **kwargs):
        super().__init__(in_q, out_q, speaker=speaker, **kwargs)
        prompt_dict = load_prompt(Config.SYSTEM_PROMPT_PATH)
        self.system_prompt = prompt_dict["prompt_text"]

    def run(self):
        print("LLM: Thread running...")
        super().run()

    def process(self, user_input):

        # Start a thread to continually play the thinking sound...
        thinking_sound_loop_stop_event = threading.Event()
        t = threading.Thread(
            target=thinking_sound_loop,
            args=(thinking_sound_loop_stop_event, self.speaker),
            daemon=True
        )
        t.start()

        # Process the streaming response from model.
        response_stream = ollama.chat(
            model=Config.OLLAMA_MODEL,
            messages=[
                {'role': 'system', 'content': self.system_prompt},
                {'role': 'user', 'content': user_input},
            ],
            stream=True,
        )
        first_token = True
        for chunk in response_stream:
            text_segment = chunk.get("message", {}).get("content")

            # If model response is ready, terminate thinking sound.
            if first_token:
                thinking_sound_loop_stop_event.set()
                first_token = False

            # Add model response to the outbound queue.
            if text_segment:
                if self.out_q:
                    self.out_q.put(text_segment)

        # Once model response completes, indicate this with a sentinel "stop" word.
        self.out_q.put("END_UTTERANCE")

        return None

