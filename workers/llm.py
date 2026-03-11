import ollama

from config import Config
from .worker_thread import WorkerThread

class LLMWorker(WorkerThread):
    """
    Listens to text queue for user inputs,
    Submits them to ollama model,
    Writes chunks of streaming response from ollama model to the  llm response queue.
    """
    def __init__(self, in_q, out_q, **kwargs):
        super().__init__(in_q, out_q, **kwargs)

    def run(self):
        print("LLM: Thread running...")
        super().run()

    def process(self, user_input):
        # print(f"LLMWorker received: {user_input}")
        response_stream = ollama.chat(
            model=Config.OLLAMA_MODEL,
            messages=[{'role': 'user', 'content': user_input}],
            stream=True,
        )
        for chunk in response_stream:
            text_segment = chunk.get("message", {}).get("content")
            if text_segment:
                if self.out_q:
                    self.out_q.put(text_segment)

        # Once model response completes, indicate this with a sentinal "stop" word.
        self.out_q.put("END_UTTERANCE")

        return None

