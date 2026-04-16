"""
Travel Agent — LangChain agent backed by a local Ollama model.

Key design decisions:
- Uses `create_react_agent` + ReAct prompting instead of OpenAI function-calling,
  because Ollama models (llama3.1, mistral, etc.) do not support the OpenAI
  functions wire format — they reason through tool use in plain text.
- The agent is stateless per request; conversation history is managed by the
  caller and injected via `chat_history`.
- Ollama runs 100% locally — no API keys, no internet required.
"""

import logging
import os
from dotenv import load_dotenv

from langchain_ollama import ChatOllama
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub

from tools.travel_tools import TOOLS
from prompts.travel_prompt import REACT_AGENT_PROMPT

load_dotenv()
logger = logging.getLogger("agent-backend.agent")


def build_agent_executor() -> AgentExecutor:
    """
    Construct a fully configured AgentExecutor ready to handle chat requests.
    Initialised once at startup and reused across requests.
    """
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model    = os.getenv("OLLAMA_MODEL", "mistral")
    temperature     = float(os.getenv("LLM_TEMPERATURE", "0.2"))

    logger.info("Building agent with Ollama model=%s at %s", ollama_model, ollama_base_url)

    # ChatOllama speaks to the locally running Ollama server.
    # stop=["Observation:"] prevents the model from hallucinating tool results —
    # it stops after writing "Action Input: X" and lets LangChain run the real tool.
    llm = ChatOllama(
        model=ollama_model,
        base_url=ollama_base_url,
        temperature=temperature,
        num_predict=2048,
        stop=["Observation:"],
    )

    # ReAct agent: the LLM reasons step-by-step in text
    # and picks tools by name (Action: get_weather \n Action Input: Paris)
    agent = create_react_agent(
        llm=llm,
        tools=TOOLS,
        prompt=REACT_AGENT_PROMPT,
    )

    executor = AgentExecutor(
        agent=agent,
        tools=TOOLS,
        verbose=True,                  # prints chain-of-thought to server logs
        max_iterations=8,              # needs room for 2 tool calls + reasoning + final answer
        return_intermediate_steps=True,
        handle_parsing_errors=True,    # recover from malformed LLM output
    )

    logger.info("AgentExecutor built | model=%s | tools=%s", ollama_model, [t.name for t in TOOLS])
    return executor


# ── Singleton executor (initialised at import time) ────────────────────────────
agent_executor = build_agent_executor()
