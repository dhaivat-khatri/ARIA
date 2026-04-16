"""
Weather Service — uses Open-Meteo API (100% free, no API key required).
Falls back to OpenWeatherMap if OPENWEATHERMAP_API_KEY is set.

Open-Meteo: https://open-meteo.com/ — free, no signup, no key needed.
"""

import os
import logging
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("mcp-server.weather")

OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "")

# Open-Meteo endpoints (no key needed)
GEOCODING_URL  = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL    = "https://api.open-meteo.com/v1/forecast"

# WMO weather interpretation codes → human-readable condition
WMO_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "foggy", 48: "icy fog",
    51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
    61: "light rain", 63: "moderate rain", 65: "heavy rain",
    71: "light snow", 73: "moderate snow", 75: "heavy snow",
    80: "light showers", 81: "moderate showers", 82: "violent showers",
    95: "thunderstorm", 96: "thunderstorm with hail", 99: "heavy thunderstorm",
}


async def fetch_weather(city: str) -> dict:
    """
    Fetch real current weather for *city*.
    Uses Open-Meteo (always free, no key) or OpenWeatherMap if key is set.
    """
    # Prefer OpenWeatherMap if key is present
    if OPENWEATHERMAP_API_KEY:
        return await _fetch_openweathermap(city)

    # Default: Open-Meteo (no key required — always real data)
    return await _fetch_open_meteo(city)


async def _fetch_open_meteo(city: str) -> dict:
    """Real weather via Open-Meteo — zero config required."""
    async with httpx.AsyncClient(timeout=10) as client:
        # Step 1: Geocode the city
        geo_resp = await client.get(
            GEOCODING_URL,
            params={"name": city, "count": 1, "language": "en", "format": "json"},
        )
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()

        results = geo_data.get("results")
        if not results:
            logger.warning("City not found in Open-Meteo geocoding: %s", city)
            return _mock_weather(city)

        loc       = results[0]
        lat       = loc["latitude"]
        lon       = loc["longitude"]
        city_name = loc.get("name", city)
        country   = loc.get("country", "")
        timezone  = loc.get("timezone", "auto")

        # Step 2: Fetch current weather
        wx_resp = await client.get(
            WEATHER_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": [
                    "temperature_2m",
                    "apparent_temperature",
                    "relative_humidity_2m",
                    "windspeed_10m",
                    "weathercode",
                    "precipitation",
                    "visibility",
                ],
                "timezone": timezone,
                "forecast_days": 1,
            },
        )
        wx_resp.raise_for_status()
        wx = wx_resp.json()["current"]

    code      = wx.get("weathercode", 0)
    condition = WMO_CODES.get(code, f"code {code}")

    result = {
        "city": city_name,
        "country": country,
        "latitude": lat,
        "longitude": lon,
        "temperature_c": round(wx["temperature_2m"], 1),
        "feels_like_c": round(wx["apparent_temperature"], 1),
        "humidity_pct": wx["relative_humidity_2m"],
        "condition": condition,
        "wind_speed_ms": round(wx["windspeed_10m"] / 3.6, 1),  # km/h → m/s
        "precipitation_mm": wx.get("precipitation", 0),
        "visibility_m": wx.get("visibility", None),
        "source": "Open-Meteo (live)",
    }

    logger.info("Weather fetched via Open-Meteo for %s: %s %.1f°C",
                city_name, condition, result["temperature_c"])
    return result


async def _fetch_openweathermap(city: str) -> dict:
    """Real weather via OpenWeatherMap (when API key is set)."""
    params = {"q": city, "appid": OPENWEATHERMAP_API_KEY, "units": "metric"}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            "https://api.openweathermap.org/data/2.5/weather", params=params
        )
        resp.raise_for_status()
        raw = resp.json()

    result = {
        "city": raw["name"],
        "country": raw["sys"]["country"],
        "temperature_c": round(raw["main"]["temp"], 1),
        "feels_like_c": round(raw["main"]["feels_like"], 1),
        "humidity_pct": raw["main"]["humidity"],
        "condition": raw["weather"][0]["description"],
        "wind_speed_ms": round(raw["wind"]["speed"], 1),
        "source": "OpenWeatherMap (live)",
    }
    logger.info("Weather fetched via OpenWeatherMap for %s", city)
    return result


# ── Emergency mock (only if geocoding fails) ──────────────────────────────────
def _mock_weather(city: str) -> dict:
    return {
        "city": city,
        "country": "",
        "temperature_c": None,
        "condition": "unavailable",
        "note": f"Could not geocode '{city}' — check spelling.",
    }
