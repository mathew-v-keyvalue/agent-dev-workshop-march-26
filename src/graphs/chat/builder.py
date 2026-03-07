from langgraph.graph import END, StateGraph

from src.graphs.chat.nodes import (
    general_assistant_agent,
    intent_agent,
    order_management_agent,
    product_discovery_agent,
)
from src.graphs.chat.states import AgentState, Intent


def _route_by_intent(state: AgentState) -> str:
    return {
        Intent.ORDER_MANAGEMENT: "order_management",
        Intent.PRODUCT_DISCOVERY: "product_discovery",
        Intent.GENERAL: "general_assistant",
    }.get(state.intent, "product_discovery")


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("intent", intent_agent)
    workflow.add_node("order_management", order_management_agent)
    workflow.add_node("product_discovery", product_discovery_agent)
    workflow.add_node("general_assistant", general_assistant_agent)

    workflow.set_entry_point("intent")
    workflow.add_conditional_edges(
        "intent",
        _route_by_intent,
        {
            "order_management": "order_management",
            "product_discovery": "product_discovery",
            "general_assistant": "general_assistant",
        },
    )
    workflow.add_edge("order_management", END)
    workflow.add_edge("product_discovery", END)
    workflow.add_edge("general_assistant", END)

    return workflow.compile()
