"""Write tools for notifications. Use execute_update from src.db."""

from langchain_core.tools import tool

from src.db import execute_query, execute_update


@tool
def mark_notification_read(notification_id: int, user_id: int) -> dict:
    """Mark a notification as read for the user.

    Args:
        notification_id: The notification ID.
        user_id: The user's ID (must own the notification).
    """
    rows = execute_query(
        "SELECT notification_id FROM notifications WHERE notification_id = %s AND user_id = %s",
        (notification_id, user_id),
    )
    if not rows:
        return {"error": "Notification not found or does not belong to this user."}
    execute_update(
        "UPDATE notifications SET is_read = 1, read_at = CURRENT_TIMESTAMP WHERE notification_id = %s AND user_id = %s",
        (notification_id, user_id),
    )
    return {"ok": True, "message": "Notification marked as read."}
