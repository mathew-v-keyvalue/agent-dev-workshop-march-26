from langchain_core.messages import HumanMessage, SystemMessage

from src.graphs.chat.builder import build_graph
from src.graphs.chat.states import AgentState

_USER_SYSTEM = (
    "The customer's user_id on KV Kart is {user_id}. "
    "Use this to look up their orders, cart, profile, etc. when needed."
)


class ChatAgent:
    def __init__(self):
        self.graph = build_graph()

    def _config(self, thread_id: str) -> dict:
        return {"configurable": {"thread_id": thread_id}}

    def _is_first_turn(self, thread_id: str) -> bool:
        state = self.graph.get_state(self._config(thread_id))
        return not state.values.get("messages")

    def _build_input(self, message: str, user_id: int, thread_id: str) -> AgentState:
        msgs = []
        if self._is_first_turn(thread_id):
            msgs.append(SystemMessage(content=_USER_SYSTEM.format(user_id=user_id)))
        msgs.append(HumanMessage(content=message))
        return AgentState(messages=msgs)

    def chat(self, message: str, thread_id: str, user_id: int) -> dict:
        return self.graph.invoke(
            self._build_input(message, user_id, thread_id),
            config=self._config(thread_id),
        )

    async def achat(self, message: str, thread_id: str, user_id: int) -> dict:
        return await self.graph.ainvoke(
            self._build_input(message, user_id, thread_id),
            config=self._config(thread_id),
        )

    def stream(self, message: str, thread_id: str, user_id: int):
        yield from self.graph.stream(
            self._build_input(message, user_id, thread_id),
            config=self._config(thread_id),
            stream_mode=["messages", "updates"],
        )

    async def astream(self, message: str, thread_id: str, user_id: int):
        async for chunk in self.graph.astream(
            self._build_input(message, user_id, thread_id),
            config=self._config(thread_id),
            stream_mode=["messages", "updates"],
        ):
            yield chunk
