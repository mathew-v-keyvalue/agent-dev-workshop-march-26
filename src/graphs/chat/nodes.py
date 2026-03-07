import asyncio
import logging

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from src.config import settings
from src.embedding.openai import OpenAIEmbedding
from src.graphs.chat.prompts import (
    GUARDRAILS_GENERAL_PROMPT,
    INTENT_CLASSIFIER_PROMPT,
    ORDER_MANAGEMENT_SYSTEM_PROMPT,
    PRODUCT_DISCOVERY_SYSTEM_PROMPT,
)
from src.graphs.chat.states import AgentState, Intent
from src.llm.openai import OpenAILLM
from src.tools import order_management_tools, product_discovery_tools
from src.tools.rag import create_rag_tools
from src.tools.search import get_web_search_tools
from src.vector_db.weaviate import WeaviateVectorDB

logger = logging.getLogger(__name__)

_llm = OpenAILLM()


def _build_order_management_tools():
    tools = list(order_management_tools)
    try:
        db = WeaviateVectorDB(url=settings.WEAVIATE_URL)
        embedding = OpenAIEmbedding()
        tools.extend(create_rag_tools(vector_db=db, embedding=embedding))
    except Exception:
        pass
    return tools


def _build_product_discovery_tools():
    tools = list(product_discovery_tools)
    tools.extend(get_web_search_tools())
    return tools


_order_mgmt_tools = _build_order_management_tools()
_product_disc_tools = _build_product_discovery_tools()

_order_react = create_agent(
    model=_llm.model,
    tools=_order_mgmt_tools,
    system_prompt=ORDER_MANAGEMENT_SYSTEM_PROMPT,
)

_product_react = create_agent(
    model=_llm.model,
    tools=_product_disc_tools,
    system_prompt=PRODUCT_DISCOVERY_SYSTEM_PROMPT,
)


def _filter_non_tool_messages(messages: list) -> list:
    """Keep only System, Human, and plain AI messages (no tool calls/results)."""
    return [
        m for m in messages
        if isinstance(m, (SystemMessage, HumanMessage))
        or (isinstance(m, AIMessage) and not m.tool_calls)
    ]


def intent_agent(state: AgentState) -> dict:
    filtered = _filter_non_tool_messages(state.messages)
    response = _llm.invoke(
        [SystemMessage(content=INTENT_CLASSIFIER_PROMPT)] + filtered,
    )
    raw = response.content.strip().upper()
    try:
        intent = Intent(raw)
    except ValueError:
        intent = Intent.PRODUCT_DISCOVERY
    logger.info("intent_agent classified=%s (raw=%r)", intent, raw)
    return {"intent": intent}


def order_management_agent(state: AgentState) -> dict:
    result = asyncio.run(
        _order_react.ainvoke({"messages": state.messages})
    )
    new_msgs = result["messages"][len(state.messages):]
    tools_used = [m.name for m in new_msgs if isinstance(m, ToolMessage)]
    if tools_used:
        logger.info("order_management_agent tools_used=%s", tools_used)
    return {"messages": new_msgs}


def product_discovery_agent(state: AgentState) -> dict:
    result = _product_react.invoke({"messages": state.messages})
    new_msgs = result["messages"][len(state.messages):]
    tools_used = [m.name for m in new_msgs if isinstance(m, ToolMessage)]
    if tools_used:
        logger.info("product_discovery_agent tools_used=%s", tools_used)
    return {"messages": new_msgs}


def general_assistant_agent(state: AgentState) -> dict:
    response = _llm.invoke(
        [SystemMessage(content=GUARDRAILS_GENERAL_PROMPT)] + state.messages,
    )
    logger.info("general_assistant_agent responded")
    return {"messages": [response]}
