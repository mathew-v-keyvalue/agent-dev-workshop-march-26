"""Read-only support ticket tools. All queries use parameterized SQL via src.db.execute_query."""

from langchain_core.tools import tool

from src.db import execute_query


@tool
def get_tickets_by_user(user_id: int, limit: int = 20) -> list:
    """Get support tickets for a user, most recent first.

    Args:
        user_id: The user's ID.
        limit: Maximum number (default 20).
    """
    rows = execute_query(
        """SELECT ticket_id, ticket_number, order_id, category, subject, priority, status, created_at, updated_at
           FROM support_tickets
           WHERE user_id = %s
           ORDER BY created_at DESC
           LIMIT %s""",
        (user_id, limit),
    )
    return rows


@tool
def get_ticket_details(ticket_id: int) -> dict:
    """Get full details of a support ticket by ID.

    Args:
        ticket_id: The ticket ID.
    """
    rows = execute_query(
        "SELECT * FROM support_tickets WHERE ticket_id = %s",
        (ticket_id,),
    )
    if not rows:
        return {"error": f"No ticket found with ticket_id {ticket_id}."}
    return rows[0]
