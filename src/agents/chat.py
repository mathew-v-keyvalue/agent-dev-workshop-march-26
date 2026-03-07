from langchain_core.messages import HumanMessage

from src.graphs.chat.builder import build_graph
from src.graphs.chat.states import AgentState


class ChatAgent:
    def __init__(self):
        self.graph = build_graph()


    def chat(self, message: str, thread_id: str, user_id: str, history=None):
        state = AgentState(messages=list(history or []) + [HumanMessage(content=message)])
        result = self.graph.invoke(state)
        return {"messages": result["messages"]}

    def stream(self, message: str, thread_id: str, user_id: str, history=None):
        state = AgentState(messages=list(history or []) + [HumanMessage(content=message)])
        yield from self.graph.stream(state, stream_mode=["messages", "updates"])
