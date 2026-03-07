from langchain_core.messages import HumanMessage, SystemMessage

from src.graphs.chat.builder import build_graph
from src.graphs.chat.states import AgentState


def _messages_with_user_context(message: str, user_id: int | str, history=None) -> list:
    """Prepend a system message with user_id so tools can use it for lookups."""
    user_context = SystemMessage(
        content=f"Current user_id for this session: {user_id}. Use this user_id for any user-scoped lookups (orders, cart, wallet, tickets, notifications, profile)."
    )
    return [user_context] + list(history or []) + [HumanMessage(content=message)]


class ChatAgent:
    def __init__(self):
        self.graph = build_graph()

    def chat(self, message: str, thread_id: str, user_id: int | str, history=None):
        state = AgentState(messages=_messages_with_user_context(message, user_id, history))
        result = self.graph.invoke(state)
        return {"messages": result["messages"]}

    def stream(self, message: str, thread_id: str, user_id: int | str, history=None):
        state = AgentState(messages=_messages_with_user_context(message, user_id, history))
        yield from self.graph.stream(state, stream_mode=["messages", "updates"])
