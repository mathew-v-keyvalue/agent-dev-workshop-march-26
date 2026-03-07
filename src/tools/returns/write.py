"""Write tools for returns. Use execute_insert, execute_update from src.db."""

from langchain_core.tools import tool

from src.db import execute_insert, execute_query, execute_update

RETURN_REASONS = {
    "defective",
    "wrong_item",
    "not_as_described",
    "size_issue",
    "changed_mind",
    "arrived_late",
    "other",
}

RETURN_STATUSES = {
    "requested",
    "approved",
    "pickup_scheduled",
    "picked_up",
    "received_at_warehouse",
    "inspected",
    "refund_initiated",
    "refund_completed",
    "rejected",
}


@tool
def create_return_request(
    order_id: int,
    order_item_id: int,
    user_id: int,
    reason: str,
    reason_detail: str | None = None,
) -> dict:
    """Create a return request for an order item. Valid reasons: defective, wrong_item, not_as_described, size_issue, changed_mind, arrived_late, other.

    Args:
        order_id: The order ID.
        order_item_id: The order item ID to return.
        user_id: The user requesting the return.
        reason: One of: defective, wrong_item, not_as_described, size_issue, changed_mind, arrived_late, other.
        reason_detail: Optional free-text detail.
    """
    reason = (reason or "").strip().lower()
    if reason not in RETURN_REASONS:
        return {"error": f"Invalid reason. Must be one of: {', '.join(sorted(RETURN_REASONS))}."}
    # Verify order_item belongs to order and user
    rows = execute_query(
        "SELECT oi.order_item_id FROM order_items oi JOIN orders o ON oi.order_id = o.order_id WHERE oi.order_id = %s AND oi.order_item_id = %s AND o.user_id = %s",
        (order_id, order_item_id, user_id),
    )
    if not rows:
        return {"error": "Order item not found or does not belong to this order/user."}
    existing = execute_query(
        "SELECT return_id FROM return_requests WHERE order_id = %s AND order_item_id = %s",
        (order_id, order_item_id),
    )
    if existing:
        return {"error": "A return request already exists for this order item."}
    execute_insert(
        """INSERT INTO return_requests (order_id, order_item_id, user_id, reason, reason_detail, return_status)
           VALUES (%s, %s, %s, %s, %s, 'requested')""",
        (order_id, order_item_id, user_id, reason, reason_detail or None),
    )
    return {"ok": True, "message": "Return request created."}


@tool
def update_return_status(return_id: int, new_status: str) -> dict:
    """Update a return request's status. Valid: requested, approved, pickup_scheduled, picked_up, received_at_warehouse, inspected, refund_initiated, refund_completed, rejected.

    Args:
        return_id: The return request ID.
        new_status: The new return_status value.
    """
    new_status = (new_status or "").strip().lower()
    if new_status not in RETURN_STATUSES:
        return {"error": f"Invalid status. Must be one of: {', '.join(sorted(RETURN_STATUSES))}."}
    rows = execute_query(
        "SELECT return_id FROM return_requests WHERE return_id = %s",
        (return_id,),
    )
    if not rows:
        return {"error": f"No return request found with return_id {return_id}."}
    execute_update(
        "UPDATE return_requests SET return_status = %s WHERE return_id = %s",
        (new_status, return_id),
    )
    return {"ok": True, "message": f"Return {return_id} status updated to '{new_status}'."}
