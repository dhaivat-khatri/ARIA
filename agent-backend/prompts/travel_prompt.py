"""
Prompt templates for the AI Travel Assistant.

ReAct format requires these exact variables in the template:
  {tools}            — descriptions of available tools
  {tool_names}       — comma-separated tool names
  {input}            — the user's message
  {agent_scratchpad} — the model's reasoning chain so far
  {chat_history}     — optional prior conversation turns
"""

from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder

# ── ReAct Prompt (Ollama / local LLMs) ────────────────────────────────────────
# Kept deliberately terse — local models follow shorter instructions more reliably.
# The output format guidance is in the Final Answer section only.
REACT_SYSTEM = """Answer the following question as best you can. You have access to these tools:

{tools}

Use the following format STRICTLY:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, must be one of [{tool_names}]
Action Input: the input to the action (city name only)
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat multiple times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

IMPORTANT:
- Always call get_weather first, then get_places.
- Never skip calling get_places.
- In your Final Answer, structure the response using this markdown format:

### 🌍 [City] Travel Guide

#### 🌤️ Weather Right Now
- **Temperature:** [X°C] (feels like [Y°C])
- **Condition:** [description]
- **Humidity:** [X]% | **Wind:** [X] m/s
- **Packing tip:** [what to wear/bring based on these conditions]

#### 📍 Top Places to Visit
[For each place: **Name** *(type)* — 2 sentences about what it is and why to go]

#### 🍽️ Food & Dining
[2 sentences on local cuisine or restaurants from the data]

#### 🧳 Quick Travel Tips
- [Transport tip]
- [Local customs tip]
- [Timing tip]

#### ❓ What would you like to know more about?
[One personalised follow-up question]

Previous chat:
{chat_history}

Question: {input}
{agent_scratchpad}"""

REACT_AGENT_PROMPT = PromptTemplate.from_template(REACT_SYSTEM)


# ── OpenAI Function-Calling Prompt (reference — not used with Ollama) ──────────
TRAVEL_AGENT_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", """You are ARIA — an expert AI travel assistant.
Always call both get_weather and get_places tools for any city question.
Structure your response with clear markdown sections: weather, places, dining, travel tips.
Be detailed and specific — minimum 250 words."""),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)
