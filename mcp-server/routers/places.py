"""Places router — exposes GET /places?city=<city>"""

import logging
from fastapi import APIRouter, HTTPException, Query
from services.places_service import fetch_places

router = APIRouter()
logger = logging.getLogger("mcp-server.places.router")


@router.get("")
async def get_places(city: str = Query(..., description="City name to get recommended places for")):
    """Return top recommended places for a given city."""
    try:
        data = await fetch_places(city)
        return data
    except Exception as exc:
        logger.error("Error fetching places for city=%s: %s", city, exc)
        raise HTTPException(status_code=502, detail=f"Places API error: {exc}") from exc
