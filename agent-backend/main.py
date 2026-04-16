"""
Agent Backend — FastAPI server exposing /chat endpoint.
Uses LangChain + OpenAI function-calling to decide which MCP tools to invoke.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chat

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)
logger = logging.getLogger("agent-backend")

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Travel Agent Backend",
    description="LangChain-powered agent that orchestrates MCP tools",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/chat", tags=["Chat"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "agent-backend"}
