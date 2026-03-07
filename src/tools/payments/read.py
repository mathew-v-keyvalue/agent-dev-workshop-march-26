"""Read-only payment tools. All queries use parameterized SQL via src.db.execute_query."""

from langchain_core.tools import tool

from src.db import execute_query


@tool
def get_payment_by_order(order_id: int) -> dict | list:
    """Get payment(s) for an order. Most orders have one payment record.

    Returns payment_method, amount, currency, payment_status, transaction_id, paid_at.

    Args:
        order_id: The internal order ID.
    """
    rows = execute_query(
        "SELECT * FROM payments WHERE order_id = %s ORDER BY payment_id",
        (order_id,),
    )
    if not rows:
        return {"error": f"No payment found for order_id {order_id}."}
    return rows[0] if len(rows) == 1 else rows


@tool
def get_payments_by_user(user_id: int, limit: int = 50) -> list:
    """List payments for a user, most recent first.

    Args:
        user_id: The user's ID.
        limit: Maximum number of payments to return (default 50).
    """
    rows = execute_query(
        "SELECT * FROM payments WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
        (user_id, limit),
    )
    return rows


@tool
def get_bulk_payments_by_orders(order_ids: list[int]) -> list:
    """Get payments for multiple orders at once. Returns list of payments (each has order_id).

    Args:
        order_ids: List of order IDs.
    """
    if not order_ids:
        return []
    placeholders = ",".join(["%s"] * len(order_ids))
    rows = execute_query(
        f"SELECT * FROM payments WHERE order_id IN ({placeholders}) ORDER BY order_id, payment_id",
        tuple(order_ids),
    )
    return rows
