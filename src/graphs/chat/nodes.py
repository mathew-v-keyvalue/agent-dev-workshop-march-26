# Add your graph nodes here

from langchain_core.messages import SystemMessage

from src.graphs.chat.prompts import SYSTEM_PROMPT
from src.graphs.chat.states import AgentState
from src.llm.openai import OpenAILLM

openai_llm = OpenAILLM()


def assistant(state: AgentState) -> dict:
    """Prepend system prompt, invoke LLM, return response in state."""
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(state.messages)
    response = openai_llm.invoke(messages)
    return {"messages": [response]}
