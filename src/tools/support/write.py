"""Write tools for support tickets. Use execute_insert, execute_update from src.db."""

from langchain_core.tools import tool

from src.db import execute_insert, execute_query, execute_update

TICKET_CATEGORIES = {
    "order_issue",
    "delivery_issue",
    "return_refund",
    "payment_issue",
    "product_complaint",
    "account_issue",
    "general_inquiry",
    "escalation",
}
TICKET_PRIORITIES = {"low", "medium", "high", "urgent"}
TICKET_STATUSES = {"open", "in_progress", "waiting_on_customer", "resolved", "closed"}


@tool
def create_support_ticket(
    user_id: int,
    category: str,
    subject: str,
    description: str,
    order_id: int | None = None,
    priority: str = "medium",
) -> dict:
    """Create a new support ticket. Category: order_issue, delivery_issue, return_refund, payment_issue, product_complaint, account_issue, general_inquiry, escalation.

    Args:
        user_id: The user creating the ticket.
        category: One of the category enum values.
        subject: Short subject line.
        description: Full description of the issue.
        order_id: Optional order ID if related to an order.
        priority: low, medium, high, or urgent (default medium).
    """
    category = (category or "").strip().lower()
    priority = (priority or "medium").strip().lower()
    if category not in TICKET_CATEGORIES:
        return {"error": f"Invalid category. Must be one of: {', '.join(sorted(TICKET_CATEGORIES))}."}
    if priority not in TICKET_PRIORITIES:
        return {"error": f"Invalid priority. Must be one of: {', '.join(sorted(TICKET_PRIORITIES))}."}
    ticket_id = execute_insert(
        """INSERT INTO support_tickets (ticket_number, user_id, order_id, category, subject, description, priority, status)
           VALUES ('PENDING', %s, %s, %s, %s, %s, %s, 'open')""",
        (user_id, order_id, category, (subject or "").strip()[:300], (description or "").strip(), priority),
    )
    execute_update(
        "UPDATE support_tickets SET ticket_number = CONCAT('TKT-', ticket_id) WHERE ticket_id = %s",
        (ticket_id,),
    )
    return {"ok": True, "ticket_id": ticket_id, "message": f"Ticket TKT-{ticket_id} created."}


@tool
def update_ticket_status(ticket_id: int, new_status: str) -> dict:
    """Update a support ticket's status. Valid: open, in_progress, waiting_on_customer, resolved, closed.

    Args:
        ticket_id: The ticket ID.
        new_status: The new status value.
    """
    new_status = (new_status or "").strip().lower()
    if new_status not in TICKET_STATUSES:
        return {"error": f"Invalid status. Must be one of: {', '.join(sorted(TICKET_STATUSES))}."}
    rows = execute_query(
        "SELECT ticket_id FROM support_tickets WHERE ticket_id = %s",
        (ticket_id,),
    )
    if not rows:
        return {"error": f"No ticket found with ticket_id {ticket_id}."}
    execute_update(
        "UPDATE support_tickets SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE ticket_id = %s",
        (new_status, ticket_id),
    )
    return {"ok": True, "message": f"Ticket {ticket_id} status updated to '{new_status}'."}
