"""Weather router — exposes GET /weather?city=<city>"""

import logging
from fastapi import APIRouter, HTTPException, Query
from services.weather_service import fetch_weather

router = APIRouter()
logger = logging.getLogger("mcp-server.weather.router")


@router.get("")
async def get_weather(city: str = Query(..., description="City name to get weather for")):
    """Return current weather data for a given city."""
    try:
        data = await fetch_weather(city)
        return data
    except Exception as exc:
        logger.error("Error fetching weather for city=%s: %s", city, exc)
        raise HTTPException(status_code=502, detail=f"Weather API error: {exc}") from exc
