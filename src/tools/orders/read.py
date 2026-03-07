"""Read-only order tools. All queries use parameterized SQL via src.db.execute_query."""

from langchain_core.tools import tool

from src.db import execute_query


@tool
def get_order_by_order_number(order_number: str) -> dict:
    """Retrieve a single order by its customer-facing order number (e.g. 'ORD-12345').

    Use this when the customer provides their order number.
    Returns order details including status, amounts, and timestamps.

    Args:
        order_number: The unique order number string shown to customers.
    """
    rows = execute_query(
        "SELECT * FROM orders WHERE order_number = %s",
        (order_number,),
    )
    if not rows:
        return {"error": f"No order found with order number '{order_number}'."}
    return rows[0]


@tool
def get_order_by_id(order_id: int) -> dict:
    """Retrieve a single order by its internal order_id.

    Use when you have the numeric order ID (e.g. from another query).

    Args:
        order_id: The internal primary key of the order.
    """
    rows = execute_query(
        "SELECT * FROM orders WHERE order_id = %s",
        (order_id,),
    )
    if not rows:
        return {"error": f"No order found with order_id {order_id}."}
    return rows[0]


@tool
def get_orders_by_user(user_id: int, limit: int = 20) -> list:
    """List orders for a user, most recent first.

    Returns up to 20 orders by default. Use for order history or "my orders" queries.

    Args:
        user_id: The user's ID.
        limit: Maximum number of orders to return (default 20).
    """
    rows = execute_query(
        "SELECT * FROM orders WHERE user_id = %s ORDER BY placed_at DESC LIMIT %s",
        (user_id, limit),
    )
    return rows


@tool
def get_order_items(order_id: int) -> list:
    """Get all line items for an order.

    Returns product_id, quantity, unit_price, total_price, item_status per line.

    Args:
        order_id: The internal order ID.
    """
    rows = execute_query(
        """SELECT oi.*, p.name AS product_name
           FROM order_items oi
           JOIN products p ON oi.product_id = p.product_id
           WHERE oi.order_id = %s ORDER BY oi.order_item_id""",
        (order_id,),
    )
    return rows


@tool
def get_order_details_full(order_id: int) -> dict:
    """Get full order details with all items (joined). Single order by order_id.

    Use when you need one order with its line items in one call.

    Args:
        order_id: The internal order ID.
    """
    orders = execute_query(
        "SELECT * FROM orders WHERE order_id = %s",
        (order_id,),
    )
    if not orders:
        return {"error": f"No order found with order_id {order_id}."}
    order = orders[0]
    order["items"] = execute_query(
        """SELECT oi.*, p.name AS product_name
           FROM order_items oi
           JOIN products p ON oi.product_id = p.product_id
           WHERE oi.order_id = %s ORDER BY oi.order_item_id""",
        (order_id,),
    )
    return order


@tool
def get_bulk_orders_by_ids(order_ids: list[int]) -> list:
    """Get multiple orders by a list of order IDs.

    Returns orders in the same order as the input list where found.
    Use when you have several order_ids (e.g. from search or user list).

    Args:
        order_ids: List of internal order IDs.
    """
    if not order_ids:
        return []
    placeholders = ",".join(["%s"] * len(order_ids))
    rows = execute_query(
        f"SELECT * FROM orders WHERE order_id IN ({placeholders})",
        tuple(order_ids),
    )
    order_by_id = {r["order_id"]: r for r in rows}
    return [order_by_id[oid] for oid in order_ids if oid in order_by_id]
