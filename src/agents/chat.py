from langchain_core.messages import HumanMessage
from src.llm.openai import OpenAILLM


class ChatAgent:
    def __init__(self):
        self.llm = OpenAILLM()

    def chat(self, message: str, thread_id: str, user_id: str, history=None):
        messages = list(history or []) + [HumanMessage(content=message)]
        response = self.llm.invoke(messages)
        return {"messages": [response]}
