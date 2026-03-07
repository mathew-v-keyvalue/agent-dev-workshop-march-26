"""Load MCP tools via langchain-mcp-adapters with SSE transport."""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from langchain_mcp_adapters.client import MultiServerMCPClient

from src.config import settings

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=1)


async def _load_tools() -> list:
    async with MultiServerMCPClient(
        {
            "kvkart-notifications": {
                "url": settings.MCP_URL,
                "transport": "sse",
            }
        }
    ) as client:
        return client.get_tools()


def get_mcp_tools() -> list:
    """Return LangChain tools from the MCP server.

    Uses a dedicated thread to avoid event-loop conflicts when called
    from within an already-running async context (e.g. LangGraph nodes).
    """
    try:
        future = _executor.submit(asyncio.run, _load_tools())
        return future.result(timeout=30)
    except Exception:
        logger.warning("Failed to load MCP tools — continuing without them", exc_info=True)
        return []
