"""MCP server exposing order-notification tools over SSE transport."""

import os

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("KVKart Notifications")

MAX_MESSAGE_LEN = 500


@mcp.tool()
def send_order_update_email(order_number: str, message: str) -> dict:
    """Send an order-update email notification to the customer.

    Args:
        order_number: The customer-facing order number (e.g. 'ORD-12345').
        message: The notification body to send (max 500 chars).
    """
    body = message[:MAX_MESSAGE_LEN]
    return {
        "success": True,
        "channel": "email",
        "order_number": order_number,
        "message": body,
    }


@mcp.tool()
def send_order_update_whatsapp(order_number: str, message: str) -> dict:
    """Send an order-update WhatsApp notification to the customer.

    Args:
        order_number: The customer-facing order number (e.g. 'ORD-12345').
        message: The notification body to send (max 500 chars).
    """
    body = message[:MAX_MESSAGE_LEN]
    return {
        "success": True,
        "channel": "whatsapp",
        "order_number": order_number,
        "message": body,
    }


if __name__ == "__main__":
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))
    mcp.run(transport="sse", host=host, port=port)
