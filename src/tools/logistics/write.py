"""Write tools for logistics. Use execute_update from src.db with parameterized queries."""

from langchain_core.tools import tool

from src.db import execute_query, execute_update

SHIPMENT_STATUSES = {
    "label_created",
    "picked_up",
    "in_transit",
    "at_hub",
    "out_for_delivery",
    "delivered",
    "failed_attempt",
    "returned_to_origin",
}


@tool
def update_shipment_status(shipment_id: int, new_status: str) -> dict:
    """Update a shipment's status.

    Allowed values: label_created, picked_up, in_transit, at_hub, out_for_delivery, delivered, failed_attempt, returned_to_origin.

    Args:
        shipment_id: The shipment ID to update.
        new_status: The new shipment_status value.
    """
    new_status = (new_status or "").strip().lower()
    if new_status not in SHIPMENT_STATUSES:
        return {"error": f"Invalid shipment status '{new_status}'."}
    rows = execute_query(
        "SELECT shipment_id FROM shipments WHERE shipment_id = %s",
        (shipment_id,),
    )
    if not rows:
        return {"error": f"No shipment found with shipment_id {shipment_id}."}
    execute_update(
        "UPDATE shipments SET shipment_status = %s, last_updated_at = CURRENT_TIMESTAMP WHERE shipment_id = %s",
        (new_status, shipment_id),
    )
    return {"ok": True, "message": f"Shipment {shipment_id} status updated to '{new_status}'."}
