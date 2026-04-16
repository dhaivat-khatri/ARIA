"""
Chat router — POST /chat

Fast 2-step pipeline (bypasses slow ReAct chain):
  Step 1: Extract city from user message (tiny LLM call, max 15 tokens)
  Step 2: Call weather + places APIs in PARALLEL
  Step 3: Single LLM synthesis call with data already injected
"""

import asyncio
import logging
from typing import List, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv
import os

load_dotenv()
router = APIRouter()
logger = logging.getLogger("agent-backend.chat")

MCP_BASE_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

# ── LLM instance ───────────────────────────────────────────────────────────────
llm = ChatOllama(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0.15,
    num_predict=800,   # cap tokens for fast responses
)

# Tiny model just for city extraction
city_llm = ChatOllama(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0,
    num_predict=15,    # only need the city name
)

# ── Request / Response Models ──────────────────────────────────────────────────

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Message]] = []

class ChatResponse(BaseModel):
    reply: str
    tools_used: List[dict] = []

# ── Helpers ────────────────────────────────────────────────────────────────────

import re

# Common travel prepositions — used for regex city extraction
_IN_PATTERN = re.compile(
    r'\b(?:in|to|for|at|near|around|visit|visiting|going to|travel(?:ling)? to|trip to|weather (?:in|at|for))\s+([A-Z][a-zA-Z\s]{1,28}?)(?:\s*[?,!.—]|$|\s+and\b|\s+weather\b|\s+places\b)',
    re.IGNORECASE
)
# Fallback: just look for a capitalised word that looks like a city
_CITY_PATTERN = re.compile(r'\b([A-Z][a-z]{2,20}(?:\s[A-Z][a-z]{2,15})?)\b')

async def extract_city(message: str) -> Optional[str]:
    """
    Fast city extraction — regex first (instant), LLM only as last resort.
    """
    # 1. Try regex with travel prepositions
    m = _IN_PATTERN.search(message)
    if m:
        city = m.group(1).strip().rstrip(",. ")
        logger.info("City via regex: %s", city)
        return city

    # 2. Try a known capitalised word
    words = message.split()
    for word in words:
        clean = word.strip(".,!?\"'")
        if clean and clean[0].isupper() and len(clean) > 2 and clean.lower() not in {
            "what", "where", "when", "how", "tell", "give", "show", "plan", "make",
            "best", "top", "good", "nice", "great", "help", "need", "want", "like",
            "please", "thanks", "there", "here", "also", "and", "for", "the",
            "weather", "places", "visit", "things", "food", "trip", "travel",
        }:
            logger.info("City via capitalised word: %s", clean)
            return clean

    # 3. LLM fallback (rare — only if all else fails)
    try:
        resp = await city_llm.ainvoke([
            SystemMessage(content="Extract ONLY the city name. Reply with city name only. If none, reply NONE."),
            HumanMessage(content=message),
        ])
        city = resp.content.strip().strip(".,!?\"'")
        if city.upper() == "NONE" or len(city) > 40:
            return None
        logger.info("City via LLM: %s", city)
        return city
    except Exception as e:
        logger.warning("City LLM extraction failed: %s", e)
        return None


async def fetch_weather(city: str) -> dict:
    """Async call to MCP weather endpoint."""
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(f"{MCP_BASE_URL}/weather", params={"city": city})
            resp.raise_for_status()
            data = resp.json()
            logger.info("[TOOL] get_weather | city=%s", city)
            return data
    except Exception as e:
        logger.error("[TOOL ERROR] get_weather: %s", e)
        return {"error": str(e)}


async def fetch_places(city: str) -> dict:
    """Async call to MCP places endpoint."""
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(f"{MCP_BASE_URL}/places", params={"city": city})
            resp.raise_for_status()
            data = resp.json()
            logger.info("[TOOL] get_places | city=%s | count=%d", city, len(data.get("places", [])))
            return data
    except Exception as e:
        logger.error("[TOOL ERROR] get_places: %s", e)
        return {"error": str(e)}


def build_synthesis_prompt(question: str, city: str, weather: dict, places: dict) -> str:
    """Build the final prompt with live data fully injected."""
    w = weather

    # Format temperature safely
    temp_str = f"{w['temperature_c']}°C" if w.get('temperature_c') is not None else "unavailable"
    feels_str = f"{w['feels_like_c']}°C" if w.get('feels_like_c') is not None else ""
    precip = w.get('precipitation_mm', 0)
    precip_str = f"{precip} mm" if precip else "none"
    vis = w.get('visibility_m')
    vis_str = f"{int(vis/1000) if vis else 0} km" if vis else ""
    source = w.get('source', 'live')

    # Format places list with descriptions
    place_lines = []
    for p in places.get("places", []):
        desc = p.get("description", "").strip()
        line = f"- **{p['name']}** ({p['category']}) — {p['address']}"
        if desc:
            line += f"\n  > {desc[:200]}"
        place_lines.append(line)
    place_list = "\n".join(place_lines) if place_lines else "No places data available."

    country = weather.get('country', '')
    city_full = f"{city}, {country}" if country else city

    return f"""You are ARIA, an expert AI travel assistant. Answer the user's question using this LIVE real-time data.

## Live Data for {city_full}
Data source: {source}

### Current Weather
- **Temperature:** {temp_str} (feels like {feels_str})
- **Condition:** {w.get('condition', 'unknown')}
- **Humidity:** {w.get('humidity_pct', '?')}%
- **Wind:** {w.get('wind_speed_ms', '?')} m/s
- **Precipitation:** {precip_str}
{f'- **Visibility:** {vis_str}' if vis_str else ''}

### Top Places & Attractions
{place_list}

## User Question
{question}

## Instructions
Write a warm, expert, structured travel guide using ONLY the real data above.
Use this markdown layout:

### 🌍 {city} Travel Guide

#### 🌤️ Weather Right Now
[Use every weather field above. Give specific packing advice based on the actual condition: "{w.get('condition', '')}"]

#### 📍 Must-Visit Places
[For each place, write 2-3 natural sentences based on its name, category, and description if available]

#### 🍽️ Food & Dining
[Write specifically about {city}'s cuisine — mention actual restaurants from the places list if any are there]

#### 🧳 Quick Travel Tips
- [Transport tip specific to {city}]
- [Local customs specific to {country or city}]
- [Best time of day tip based on current weather]

#### ❓ What would you like to plan next?
[One specific follow-up question]

Be concise but rich in detail. 250-350 words."""


# ── Endpoint ───────────────────────────────────────────────────────────────────

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    logger.info("Message: %r", request.message)

    # ── Step 1: Extract city ───────────────────────────────────────────────────
    city = await extract_city(request.message)

    tools_used = []

    if city:
        # ── Step 2: Parallel API calls ─────────────────────────────────────────
        weather_data, places_data = await asyncio.gather(
            fetch_weather(city),
            fetch_places(city),
        )
        tools_used = [
            {"tool": "get_weather", "input": {"city": city}, "output": str(weather_data)[:300]},
            {"tool": "get_places",  "input": {"city": city}, "output": str(places_data)[:300]},
        ]
        prompt = build_synthesis_prompt(request.message, city, weather_data, places_data)
    else:
        # No city found — ask user to clarify
        prompt = f"""You are ARIA, a friendly travel assistant.
The user sent: "{request.message}"
No specific city was mentioned. Ask them politely to specify a destination city so you can provide live weather and place recommendations.
Keep your response under 50 words."""

    # ── Step 3: Build chat history ─────────────────────────────────────────────
    lc_history = []
    for msg in (request.history or [])[-6:]:   # last 3 turns only, keeps context short
        if msg.role == "human":
            lc_history.append(HumanMessage(content=msg.content))
        else:
            lc_history.append(AIMessage(content=msg.content))

    # ── Step 4: Single LLM synthesis call ─────────────────────────────────────
    try:
        messages = lc_history + [HumanMessage(content=prompt)]
        result = await llm.ainvoke(messages)
        reply = result.content.strip()
    except Exception as exc:
        logger.error("LLM synthesis failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"LLM error: {exc}") from exc

    logger.info("Reply generated | len=%d | city=%s", len(reply), city)
    return ChatResponse(reply=reply, tools_used=tools_used)
