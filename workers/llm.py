import threading
import uuid
from typing import List

from langchain.agents import create_agent, AgentState
from langchain.chat_models import init_chat_model
from langchain_community.tools import BraveSearch
from langchain_core.messages import AIMessageChunk
from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver


from config import Config
from utils import load_prompt, thinking_sound_loop, load_wav_pcm, convert_message_list_to_string
from .worker_thread import WorkerThread


brave_search_tool = BraveSearch.from_search_kwargs(search_kwargs={
    "count": 3,
    "country": "us",
})

agent_tools = [
    brave_search_tool,
]


# Define a schema for the agent; what additional params to expect.
class AgentStateSchema(AgentState):
    user_intent: str


class LLMWorker(WorkerThread):
    """
    Listens to text queue for user inputs,
    Submits them to ollama model,
    Writes chunks of streaming response from ollama model to the llm response queue.
    """
    def __init__(self, in_q, out_q, speaker, audio_playback_queue, **kwargs):
        super().__init__(in_q, out_q, speaker=speaker, audio_playback_queue=audio_playback_queue, **kwargs)
        self.thinking_sound_pcm = load_wav_pcm(Config.PATH_TO_THINKING_SOUND)
        self.model = ChatOllama(
                model=Config.OLLAMA_MODEL,
                validate_model_on_init=True,
        )
        self.agent = create_agent(
            model=self.model,
            tools=agent_tools,
            system_prompt=load_prompt("system_prompt").get("prompt_text", {}),
            checkpointer=InMemorySaver(),
            state_schema=AgentStateSchema,
        )
        self.current_session_id = str(uuid.uuid4())

    def run(self):
        print("LLM: Thread running...")
        super().run()

    def process(self, user_input):

        # Start a thread to continually play the thinking sound...
        thinking_sound_loop_stop_event = threading.Event()
        t = threading.Thread(
            target=thinking_sound_loop,
            args=(thinking_sound_loop_stop_event, self.audio_playback_queue, self.thinking_sound_pcm),
            daemon=True
        )
        t.start()

        # Get chat history to add conversational context to user intent extraction.
        state = self.agent.get_state(
            config={"configurable": {"thread_id": self.current_session_id}}
        )
        recent_messages = state.values.get("messages", [])[-5:]
        context_messages_as_text = convert_message_list_to_string(recent_messages)

        # Get the user's actual intention
        user_intent_prompt_text = load_prompt("user_intent_extraction").get("prompt_text", {})
        user_intent_prompt = PromptTemplate(
            template=user_intent_prompt_text,
            input_variables=["most_recent_chat_history", "user_input"],
        )
        input_variables = {
            "most_recent_chat_history": context_messages_as_text,
            "user_input": user_input,
        }
        intent_chain = user_intent_prompt | self.model
        user_intent_statement = intent_chain.invoke(input_variables).content

        print(f"user intent: {user_intent_statement}")

        # Process the streaming response from model.
        response_stream = self.agent.stream(
            input={
                "messages": [{"role": "user", "content": user_input}],
                "user_intent": user_intent_statement,
            },
            config={"configurable": {"thread_id": self.current_session_id}},
            stream_mode="messages",
        )

        first_token = True
        for chunk in response_stream:

            if first_token:
                thinking_sound_loop_stop_event.set()
                self.audio_playback_queue.put(("clear_thinking", None))
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

