"""Read-only logistics tools. All queries use parameterized SQL via src.db.execute_query."""

from langchain_core.tools import tool

from src.db import execute_query


@tool
def get_shipment_by_order(order_id: int) -> dict | list:
    """Get shipment(s) for an order. Most orders have one shipment.

    Returns shipment details including awb_number, status, estimated_delivery_date, last_location.

    Args:
        order_id: The internal order ID.
    """
    rows = execute_query(
        """SELECT s.*, lp.name AS partner_name, lp.tracking_url_template
           FROM shipments s
           LEFT JOIN logistics_partners lp ON s.logistics_partner_id = lp.partner_id
           WHERE s.order_id = %s ORDER BY s.shipment_id""",
        (order_id,),
    )
    if not rows:
        return {"error": f"No shipment found for order_id {order_id}."}
    return rows[0] if len(rows) == 1 else rows


@tool
def get_tracking_events(shipment_id: int) -> list:
    """Get tracking events for a shipment, ordered by time (oldest first).

    Args:
        shipment_id: The shipment ID.
    """
    rows = execute_query(
        """SELECT event_id, shipment_id, event_status, location, description, event_timestamp
           FROM shipment_tracking_events
           WHERE shipment_id = %s ORDER BY event_timestamp ASC""",
        (shipment_id,),
    )
    return rows


@tool
def get_full_tracking_by_order(order_id: int) -> dict:
    """Get shipment and all tracking events for an order in one call.

    Returns shipment info plus a list of tracking events.

    Args:
        order_id: The internal order ID.
    """
    shipments = execute_query(
        """SELECT s.*, lp.name AS partner_name, lp.tracking_url_template
           FROM shipments s
           LEFT JOIN logistics_partners lp ON s.logistics_partner_id = lp.partner_id
           WHERE s.order_id = %s ORDER BY s.shipment_id""",
        (order_id,),
    )
    if not shipments:
        return {"error": f"No shipment found for order_id {order_id}."}
    shipment = shipments[0]
    shipment["tracking_events"] = execute_query(
        """SELECT event_status, location, description, event_timestamp
           FROM shipment_tracking_events
           WHERE shipment_id = %s ORDER BY event_timestamp ASC""",
        (shipment["shipment_id"],),
    )
    return shipment


@tool
def get_delivery_estimate(origin_pincode: str, destination_pincode: str) -> list:
    """Get delivery time estimates between two pincodes (optionally by logistics partner).

    Returns estimated_days_min, estimated_days_max, partner info for serviceable routes.

    Args:
        origin_pincode: Origin pincode (e.g. '560001').
        destination_pincode: Destination pincode (e.g. '400001').
    """
    rows = execute_query(
        """SELECT de.*, lp.name AS partner_name
           FROM delivery_estimates de
           JOIN logistics_partners lp ON de.logistics_partner_id = lp.partner_id
           WHERE de.origin_pincode = %s AND de.destination_pincode = %s
             AND de.is_serviceable = 1 AND lp.is_active = 1""",
        (origin_pincode.strip(), destination_pincode.strip()),
    )
    return rows


@tool
def get_logistics_partners() -> list:
    """List active logistics partners with name, tracking_url_template, avg_delivery_days."""
    rows = execute_query(
        """SELECT partner_id, name, tracking_url_template, avg_delivery_days
           FROM logistics_partners WHERE is_active = 1 ORDER BY name"""
    )
    return rows


@tool
def get_bulk_shipments_by_orders(order_ids: list[int]) -> list:
    """Get shipments for multiple orders at once. Returns list of shipments (each has order_id).

    Args:
        order_ids: List of order IDs.
    """
    if not order_ids:
        return []
    placeholders = ",".join(["%s"] * len(order_ids))
    rows = execute_query(
        f"""SELECT s.*, lp.name AS partner_name
            FROM shipments s
            LEFT JOIN logistics_partners lp ON s.logistics_partner_id = lp.partner_id
            WHERE s.order_id IN ({placeholders})
            ORDER BY s.order_id, s.shipment_id""",
        tuple(order_ids),
    )
    return rows
