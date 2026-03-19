import threading
import time
import uuid

from langchain.agents import create_agent
from langchain_community.tools import BraveSearch, WikipediaQueryRun, ArxivQueryRun, PubmedQueryRun
from langchain_community.utilities import WikipediaAPIWrapper, ArxivAPIWrapper
from langchain_core.messages import AIMessageChunk
from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver


from config import Config
from utils import load_prompt, thinking_sound_loop, load_wav_pcm
from .worker_thread import WorkerThread


brave_search_tool = BraveSearch.from_search_kwargs(search_kwargs={
    "count": 10,
    "country": "us",
})

wikipedia_search_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

arxiv_search_tool = ArxivQueryRun(api_wrapper=ArxivAPIWrapper())

pub_med_search_tool = PubmedQueryRun()

agent_tools = [
    brave_search_tool,
    wikipedia_search_tool,
    arxiv_search_tool,
    pub_med_search_tool,
]

system_prompt_template_text = load_prompt("system_prompt").get("prompt_text", {})
system_prompt_string = PromptTemplate(
    template=system_prompt_template_text,
    input_variables=["current_date", "current_location"],
).partial(
    current_date=time.strftime("%B %d, %Y"),
    current_location=Config.CURRENT_LOCATION,
).format()


class LLMWorker(WorkerThread):
    """
    Listens to text queue for user inputs,
    Submits them to ollama model,
    Writes chunks of streaming response from ollama model to the llm response queue.
    """
    def __init__(self, in_q, out_q, audio_playback_queue, **kwargs):
        super().__init__(in_q, out_q, audio_playback_queue=audio_playback_queue, **kwargs)
        self.model = ChatOllama(
                model=Config.OLLAMA_MODEL,
                validate_model_on_init=True,
        )
        self.agent = create_agent(
            model=self.model,
            tools=agent_tools,
            system_prompt=system_prompt_string,
            checkpointer=InMemorySaver(),
        )
        self.current_session_id = str(uuid.uuid4())

    def run(self):
        print("LLM: Thread running...")
        super().run()

    def process(self, user_input):

        self.audio_playback_queue.put(("start_thinking", None))

        response_stream = self.agent.stream(
            input={
                "messages": [{"role": "user", "content": user_input}],
            },
            config={"configurable": {"thread_id": self.current_session_id}},
            stream_mode="messages",
        )

        is_first_token_of_response = True
        for chunk in response_stream:

            message = chunk[0] # Chunks are tuples
            if not message:
                continue

            is_user_facing_response = bool(message.content) and isinstance(message, AIMessageChunk)

            if is_user_facing_response and is_first_token_of_response:
                self.audio_playback_queue.put(("done_thinking", None))
                is_first_token_of_response = False

            # Printing activity for debugging visibility
            if is_user_facing_response:
                print(f"Agent: {message.content}")
            elif hasattr(message, "tool_calls"):
                print(f"Calling tools: {[tc['name'] for tc in message.tool_calls]}")

            # Add model response to the outbound queue.
            if message and message.content and isinstance(message, AIMessageChunk):
                if self.out_q:
                    self.out_q.put(message.content)

        # Once model response completes, indicate this with a sentinel "stop" word.
        self.out_q.put("END_UTTERANCE")

        return None

