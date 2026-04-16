"""
Tool definitions for the LangChain agent.

Each tool wraps one MCP server endpoint.
Tools are async so they don't block the event loop.
Tool calls are logged for observability.
"""

import logging
import httpx
from langchain.tools import tool

logger = logging.getLogger("agent-backend.tools")

# ── MCP Server base URL ────────────────────────────────────────────────────────
import os
from dotenv import load_dotenv

load_dotenv()
MCP_BASE_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001")


# ── Weather Tool ───────────────────────────────────────────────────────────────

@tool
async def get_weather(city: str) -> str:
    """
    Get the current weather for a city.
    Use this tool when the user asks about weather, temperature,
    climate, what to wear, or whether it will rain.

    Args:
        city: The name of the city (e.g. 'Paris', 'Tokyo').

    Returns:
        A JSON-formatted string with weather details.
    """
    logger.info("[TOOL CALL] get_weather | city=%s", city)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{MCP_BASE_URL}/weather", params={"city": city})
            resp.raise_for_status()
            data = resp.json()

        logger.info("[TOOL RESULT] get_weather | city=%s → %s", city, data)
        return str(data)

    except httpx.HTTPStatusError as exc:
        logger.error("[TOOL ERROR] get_weather | %s", exc)
        return f"Error fetching weather: {exc.response.status_code}"
    except Exception as exc:
        logger.error("[TOOL ERROR] get_weather | %s", exc)
        return f"Unexpected error: {exc}"


# ── Places Tool ────────────────────────────────────────────────────────────────

@tool
async def get_places(city: str) -> str:
    """
    Get top recommended places to visit in a city.
    Use this tool when the user asks about things to do, attractions,
    restaurants, nightlife, tourist spots, or travel recommendations.

    Args:
        city: The name of the city (e.g. 'Paris', 'Tokyo').

    Returns:
        A JSON-formatted string listing recommended venues.
    """
    logger.info("[TOOL CALL] get_places | city=%s", city)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{MCP_BASE_URL}/places", params={"city": city})
            resp.raise_for_status()
            data = resp.json()

        logger.info("[TOOL RESULT] get_places | city=%s → %d places", city, len(data.get("places", [])))
        return str(data)

    except httpx.HTTPStatusError as exc:
        logger.error("[TOOL ERROR] get_places | %s", exc)
        return f"Error fetching places: {exc.response.status_code}"
    except Exception as exc:
        logger.error("[TOOL ERROR] get_places | %s", exc)
        return f"Unexpected error: {exc}"


# ── Exported list of all tools ─────────────────────────────────────────────────
TOOLS = [get_weather, get_places]
