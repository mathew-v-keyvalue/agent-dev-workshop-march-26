from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from src.graphs.chat.nodes import (
    agent_guardrails_agent,
    general_assistant_agent,
    intent_agent,
    order_management_agent,
    product_discovery_agent,
    user_guardrails_agent,
)
from src.graphs.chat.states import AgentState, Intent


def _route_after_user_guardrails(state: AgentState) -> str:
    if state.user_guardrail_flag:
        return END
    return "intent"


def _route_by_intent(state: AgentState) -> str:
    return {
        Intent.ORDER_MANAGEMENT: "order_management",
        Intent.PRODUCT_DISCOVERY: "product_discovery",
        Intent.GENERAL: "general_assistant",
    }.get(state.intent, "product_discovery")


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("user_guardrails", user_guardrails_agent)
    workflow.add_node("intent", intent_agent)
    workflow.add_node("order_management", order_management_agent)
    workflow.add_node("product_discovery", product_discovery_agent)
    workflow.add_node("general_assistant", general_assistant_agent)
    workflow.add_node("agent_guardrails", agent_guardrails_agent)

    workflow.set_entry_point("user_guardrails")
    workflow.add_conditional_edges(
        "user_guardrails",
        _route_after_user_guardrails,
        {"intent": "intent", END: END},
    )
    workflow.add_conditional_edges(
        "intent",
        _route_by_intent,
        {
            "order_management": "order_management",
            "product_discovery": "product_discovery",
            "general_assistant": "general_assistant",
        },
    )
    workflow.add_edge("order_management", "agent_guardrails")
    workflow.add_edge("product_discovery", "agent_guardrails")
    workflow.add_edge("general_assistant", "agent_guardrails")
    workflow.add_edge("agent_guardrails", END)

    return workflow.compile(checkpointer=MemorySaver())
