"""
MCP Server — Acts as a wrapper over external APIs (weather + places).
Exposes RESTful endpoints consumed by the Agent Backend.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import weather, places

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)
logger = logging.getLogger("mcp-server")

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Travel MCP Server",
    description="Model Context Protocol server wrapping weather & places APIs",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(weather.router, prefix="/weather", tags=["Weather"])
app.include_router(places.router, prefix="/places", tags=["Places"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "mcp-server"}
