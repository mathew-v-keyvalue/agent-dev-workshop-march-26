"""Read-only return and refund tools. All queries use parameterized SQL via src.db.execute_query."""

from langchain_core.tools import tool

from src.db import execute_query


@tool
def get_return_requests_by_order(order_id: int) -> list:
    """Get all return requests for an order.

    Args:
        order_id: The order ID.
    """
    rows = execute_query(
        """SELECT rr.*, oi.product_id, p.name AS product_name
           FROM return_requests rr
           JOIN order_items oi ON rr.order_item_id = oi.order_item_id
           JOIN products p ON oi.product_id = p.product_id
           WHERE rr.order_id = %s
           ORDER BY rr.requested_at DESC""",
        (order_id,),
    )
    return rows


@tool
def get_return_requests_by_user(user_id: int, limit: int = 20) -> list:
    """Get return requests for a user, most recent first.

    Args:
        user_id: The user's ID.
        limit: Maximum number to return (default 20).
    """
    rows = execute_query(
        """SELECT rr.*, o.order_number, oi.product_id, p.name AS product_name
           FROM return_requests rr
           JOIN orders o ON rr.order_id = o.order_id
           JOIN order_items oi ON rr.order_item_id = oi.order_item_id
           JOIN products p ON oi.product_id = p.product_id
           WHERE rr.user_id = %s
           ORDER BY rr.requested_at DESC
           LIMIT %s""",
        (user_id, limit),
    )
    return rows


@tool
def get_refund_by_order(order_id: int) -> dict | list:
    """Get refund(s) for an order.

    Args:
        order_id: The order ID.
    """
    rows = execute_query(
        "SELECT * FROM refunds WHERE order_id = %s ORDER BY initiated_at DESC",
        (order_id,),
    )
    if not rows:
        return {"error": f"No refund found for order_id {order_id}."}
    return rows[0] if len(rows) == 1 else rows


@tool
def get_refund_by_user(user_id: int, limit: int = 20) -> list:
    """Get refunds for a user, most recent first.

    Args:
        user_id: The user's ID.
        limit: Maximum number (default 20).
    """
    rows = execute_query(
        """SELECT r.*, o.order_number
           FROM refunds r
           JOIN orders o ON r.order_id = o.order_id
           WHERE r.user_id = %s
           ORDER BY r.initiated_at DESC
           LIMIT %s""",
        (user_id, limit),
    )
    return rows


@tool
def get_refund_status(refund_id: int) -> dict:
    """Get status and details of a refund by refund_id.

    Args:
        refund_id: The refund ID.
    """
    rows = execute_query(
        "SELECT * FROM refunds WHERE refund_id = %s",
        (refund_id,),
    )
    if not rows:
        return {"error": f"No refund found with refund_id {refund_id}."}
    return rows[0]
