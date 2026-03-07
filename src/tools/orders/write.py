"""Write tools for orders. Use execute_update from src.db with parameterized queries."""

from langchain_core.tools import tool

from src.db import execute_query, execute_update

# Valid status transitions: from_status -> set of allowed to_status
ORDER_STATUS_TRANSITIONS = {
    "pending": {"confirmed", "cancelled", "failed"},
    "confirmed": {"processing", "cancelled"},
    "processing": {"shipped", "cancelled"},
    "shipped": {"out_for_delivery"},
    "out_for_delivery": {"delivered", "failed"},
    "delivered": {"return_requested"},
    "cancelled": set(),
    "return_requested": set(),
    "returned": set(),
    "failed": set(),
}

CANCELLABLE_STATUSES = {"pending", "confirmed", "processing"}


@tool
def cancel_order(order_id: int, reason: str | None = None) -> dict:
    """Cancel an order. Only allowed when status is pending, confirmed, or processing and is_cancellable is true.

    Args:
        order_id: The internal order ID to cancel.
        reason: Optional cancellation reason (stored in cancellation_reason).
    """
    rows = execute_query(
        "SELECT order_id, order_status, is_cancellable FROM orders WHERE order_id = %s",
        (order_id,),
    )
    if not rows:
        return {"error": f"No order found with order_id {order_id}."}
    row = rows[0]
    status = (row.get("order_status") or "").lower()
    cancellable = row.get("is_cancellable")
    if status not in CANCELLABLE_STATUSES:
        return {"error": f"Order cannot be cancelled: current status is '{status}'."}
    if not cancellable:
        return {"error": "Order is not cancellable."}
    execute_update(
        "UPDATE orders SET order_status = 'cancelled', cancelled_at = CURRENT_TIMESTAMP, cancellation_reason = %s WHERE order_id = %s",
        (reason or None, order_id),
    )
    return {"ok": True, "message": f"Order {order_id} has been cancelled."}


@tool
def update_order_status(order_id: int, new_status: str) -> dict:
    """Update an order's status. Only allowed transitions are enforced.

    Valid transitions:
    - pending -> confirmed, cancelled, failed
    - confirmed -> processing, cancelled
    - processing -> shipped, cancelled
    - shipped -> out_for_delivery
    - out_for_delivery -> delivered, failed
    - delivered -> return_requested

    Args:
        order_id: The internal order ID.
        new_status: One of: pending, confirmed, processing, shipped, out_for_delivery, delivered, cancelled, return_requested, returned, failed.
    """
    new_status = (new_status or "").strip().lower()
    allowed = {
        "pending", "confirmed", "processing", "shipped", "out_for_delivery",
        "delivered", "cancelled", "return_requested", "returned", "failed",
    }
    if new_status not in allowed:
        return {"error": f"Invalid status '{new_status}'."}
    rows = execute_query(
        "SELECT order_id, order_status FROM orders WHERE order_id = %s",
        (order_id,),
    )
    if not rows:
        return {"error": f"No order found with order_id {order_id}."}
    current = (rows[0].get("order_status") or "").lower()
    if current not in ORDER_STATUS_TRANSITIONS:
        return {"error": f"Unknown current status '{current}'."}
    if new_status not in ORDER_STATUS_TRANSITIONS[current]:
        return {"error": f"Transition from '{current}' to '{new_status}' is not allowed."}
    execute_update(
        "UPDATE orders SET order_status = %s WHERE order_id = %s",
        (new_status, order_id),
    )
    return {"ok": True, "message": f"Order {order_id} status updated to '{new_status}'."}
