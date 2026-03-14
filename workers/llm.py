import threading
import uuid
from typing import List

from langchain.agents import create_agent
from langchain_core.messages import AIMessageChunk
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from langchain.tools import tool

from config import Config
from utils import load_prompt, thinking_sound_loop, load_wav_pcm
from .worker_thread import WorkerThread


@tool
def validate_user(user_id: int, addresses: List[str]) -> bool:
    """Validate user using historical addresses.

    Args:
        user_id (int): the user ID.
        addresses (List[str]): Previous addresses as a list of strings.
    """
    return True


class LLMWorker(WorkerThread):
    """
    Listens to text queue for user inputs,
    Submits them to ollama model,
    Writes chunks of streaming response from ollama model to the llm response queue.
    """
    def __init__(self, in_q, out_q, speaker, audio_queue, **kwargs):
        super().__init__(in_q, out_q, speaker=speaker, audio_queue=audio_queue, **kwargs)
        self.thinking_sound_pcm = load_wav_pcm(Config.PATH_TO_THINKING_SOUND)
        self.agent = create_agent(
            model=ChatOllama(
                model=Config.OLLAMA_MODEL,
                validate_model_on_init=True,
            ),
            tools=[validate_user],
            system_prompt=load_prompt(Config.SYSTEM_PROMPT_PATH).get("prompt_text", {}),
            checkpointer=InMemorySaver(),
        )

    def run(self):
        print("LLM: Thread running...")
        super().run()

    def process(self, user_input):

        # Start a thread to continually play the thinking sound...
        thinking_sound_loop_stop_event = threading.Event()
        t = threading.Thread(
            target=thinking_sound_loop,
            args=(thinking_sound_loop_stop_event, self.audio_queue, self.thinking_sound_pcm),
            daemon=True
        )
        t.start()

        # Process the streaming response from model.
        response_stream = self.agent.stream(
            input={"messages": [{"role": "user", "content": user_input}]},
            config={"configurable": {"thread_id": str(uuid.uuid4())}},
            stream_mode="messages",
        )

        first_token = True
        for chunk in response_stream:

            if first_token:
                thinking_sound_loop_stop_event.set()
                self.audio_queue.put(("clear_thinking", None))
                first_token = False

            token_chunk = chunk[0] # Chunks are tuples
            if not token_chunk:
                continue

            # Printing activity for debugging visibility
            if token_chunk.content:
                if isinstance(token_chunk, AIMessageChunk):
                    print(f"Agent: {token_chunk.content}")
            elif token_chunk.tool_calls:
                print(f"Calling tools: {[tc['name'] for tc in token_chunk.tool_calls]}")

            # Add model response to the outbound queue.
            if token_chunk and token_chunk.content and isinstance(token_chunk, AIMessageChunk):
                if self.out_q:
                    self.out_q.put(token_chunk.content)

        # Once model response completes, indicate this with a sentinel "stop" word.
        self.out_q.put("END_UTTERANCE")

        return None

