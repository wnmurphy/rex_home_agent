import ollama

from config import Config
from utils import load_prompt
from .worker_thread import WorkerThread

class LLMWorker(WorkerThread):
    """
    Listens to text queue for user inputs,
    Submits them to ollama model,
    Writes chunks of streaming response from ollama model to the llm response queue.
    """
    def __init__(self, in_q, out_q, **kwargs):
        super().__init__(in_q, out_q, **kwargs)
        prompt_dict = load_prompt(Config.SYSTEM_PROMPT_PATH)
        self.system_prompt = prompt_dict["prompt_text"]

    def run(self):
        print("LLM: Thread running...")
        super().run()

    def process(self, user_input):
        response_stream = ollama.chat(
            model=Config.OLLAMA_MODEL,
            messages=[
                {'role': 'system', 'content': self.system_prompt},
                {'role': 'user', 'content': user_input},
            ],
            stream=True,
        )
        for chunk in response_stream:
            text_segment = chunk.get("message", {}).get("content")
            if text_segment:
                if self.out_q:
                    self.out_q.put(text_segment)

        # Once model response completes, indicate this with a sentinel "stop" word.
        self.out_q.put("END_UTTERANCE")

        return None

