import asyncio
import logging

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from pydantic import BaseModel, Field

from src.config import settings
from src.embedding.openai import OpenAIEmbedding
from src.graphs.chat.prompts import (
    AGENT_GUARDRAILS_PROMPT,
    GUARDRAILS_GENERAL_PROMPT,
    INTENT_CLASSIFIER_PROMPT,
    ORDER_MANAGEMENT_SYSTEM_PROMPT,
    PRODUCT_DISCOVERY_SYSTEM_PROMPT,
    USER_GUARDRAILS_PROMPT,
)
from src.graphs.chat.states import AgentState, Intent
from src.llm.openai import OpenAILLM
from src.tools import order_management_tools, product_discovery_tools
from src.tools.mcp import get_mcp_tools
from src.tools.rag import create_rag_tools
from src.tools.search import get_web_search_tools
from src.vector_db.weaviate import WeaviateVectorDB

logger = logging.getLogger(__name__)

_llm = OpenAILLM()


class GuardrailResult(BaseModel):
    content: str = Field(description="The response content or refusal message")
    flag: bool = Field(description="True if blocked/unsafe, False if allowed/safe")


_user_guardrail_llm = _llm.model.with_structured_output(GuardrailResult)
_agent_guardrail_llm = _llm.model.with_structured_output(GuardrailResult)


def _build_order_management_tools():
    tools = list(order_management_tools)
    try:
        db = WeaviateVectorDB(url=settings.WEAVIATE_URL)
        embedding = OpenAIEmbedding()
        tools.extend(create_rag_tools(vector_db=db, embedding=embedding))
    except Exception:
        pass
    tools.extend(get_mcp_tools())
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


def user_guardrails_agent(state: AgentState) -> dict:
    last_human = None
    for m in reversed(state.messages):
        if isinstance(m, HumanMessage):
            last_human = m
            break
    if last_human is None:
        return {"user_guardrail_flag": False}

    context = [
        m for m in state.messages
        if isinstance(m, (SystemMessage, HumanMessage))
        or (isinstance(m, AIMessage) and not m.tool_calls)
    ][-10:]

    result: GuardrailResult = _user_guardrail_llm.invoke(
        [SystemMessage(content=USER_GUARDRAILS_PROMPT)] + context,
    )
    logger.info("user_guardrails_agent flag=%s", result.flag)

    if result.flag:
        return {
            "user_guardrail_flag": True,
            "messages": [AIMessage(content=result.content)],
        }
    return {"user_guardrail_flag": False}


def agent_guardrails_agent(state: AgentState) -> dict:
    candidate = None
    for m in reversed(state.messages):
        if isinstance(m, AIMessage) and m.content and not m.tool_calls:
            candidate = m
            break
    if candidate is None:
        return {"agent_response_safe": True}

    context = [
        m for m in state.messages
        if isinstance(m, (SystemMessage, HumanMessage))
        or (isinstance(m, AIMessage) and not m.tool_calls)
    ][-10:]

    result: GuardrailResult = _agent_guardrail_llm.invoke(
        [SystemMessage(content=AGENT_GUARDRAILS_PROMPT)] + context,
    )
    logger.info("agent_guardrails_agent flag=%s", result.flag)

    if result.flag:
        return {
            "agent_response_safe": False,
            "messages": [AIMessage(content="I'm sorry, something went wrong. Please try again.")],
        }

    if result.content != candidate.content:
        return {
            "agent_response_safe": True,
            "messages": [AIMessage(content=result.content)],
        }
    return {"agent_response_safe": True}
