"""Read-only notification tools. All queries use parameterized SQL via src.db.execute_query."""

from langchain_core.tools import tool

from src.db import execute_query


@tool
def get_user_notifications(user_id: int, limit: int = 20, unread_only: bool = False) -> list:
    """Get notifications for a user, most recent first.

    Args:
        user_id: The user's ID.
        limit: Maximum number (default 20).
        unread_only: If True, return only unread notifications.
    """
    if unread_only:
        rows = execute_query(
            """SELECT notification_id, type, title, message, reference_type, reference_id, is_read, sent_at
               FROM notifications
               WHERE user_id = %s AND is_read = 0
               ORDER BY sent_at DESC
               LIMIT %s""",
            (user_id, limit),
        )
    else:
        rows = execute_query(
            """SELECT notification_id, type, title, message, reference_type, reference_id, is_read, sent_at, read_at
               FROM notifications
               WHERE user_id = %s
               ORDER BY sent_at DESC
               LIMIT %s""",
            (user_id, limit),
        )
    return rows
