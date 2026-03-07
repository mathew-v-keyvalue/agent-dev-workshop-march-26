# Add your graph nodes here

from langchain.agents import create_agent

from src.graphs.chat.prompts import SYSTEM_PROMPT
from src.graphs.chat.states import AgentState
from src.llm.openai import OpenAILLM
from src.tools import all_tools

_openai = OpenAILLM()
_react_agent = create_agent(
    _openai.model,
    tools=all_tools,
    system_prompt=SYSTEM_PROMPT,
)


def assistant(state: AgentState) -> dict:
    """Run the ReAct agent with all_tools; return only new messages for state."""
    input_messages = list(state.messages)
    result = _react_agent.invoke({"messages": input_messages})
    new_messages = result["messages"][len(input_messages):]
    return {"messages": new_messages}
