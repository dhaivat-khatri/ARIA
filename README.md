# ARIA — Agentic Real-time Intelligence Assistant 🌍✈️

**A production-grade, fully local AI travel assistant built with a multi-service architecture seamlessly orchestrating an MCP Server, a LangChain-powered Agent Backend, and a premium React Frontend.**

---

## 🎥 Video Demonstration & Evaluation Guide

*This section serves as the formal outline for the video presentation component of the evaluation, detailing the agentic development approach, architectural constraints, and deployment strategies.*

### 1. Approach & Agentic IDE Prompts
The development of ARIA was heavily accelerated using an agentic IDE approach, treating the AI as an active collaborative partner. The approach was segmented into three iterative layers:

**Prompt Flow Examples:**
- **MCP Server Wrapper:**
  > *"Build a FastAPI-based MCP (Model Context Protocol) server with clean service-layer separation. Implement two endpoints: `/weather` and `/places`. Use Open-Meteo and Overpass API (OpenStreetMap) to ensure 100% free, factual, global coverage without requiring API keys. Include robust error handling and fallback mirrors for high availability."*
- **LLM Agent Setup (Tool Calling):**
  > *"Create a LangChain agent using `ChatOllama` for a fully local pipeline. Since ReAct paradigms can be slow, refactor the chain into a rapid 2-step parallel pipeline: first, asynchronously extract the city intent, then fire both MCP tools simultaneously, and finally synthesise the data into a strict, markdown-formatted final answer."*
- **Frontend & UX Formulation:**
  > *"Develop a premium React frontend leveraging Vite. Implement a sleek dark mode with CSS glassmorphism, dynamic animations, and `react-markdown` to parse and beautifully render the agent's complex structured output. Include tool badges that dynamically display when the agent accesses external databases."*

### 2. Architectural Overview
ARIA adopts a modern, decoupled microservices architecture. It ensures extreme resilience, security, and scalability.

- **MCP Server (Port 8001):** Acts as the secure boundary isolating external APIs (Open-Meteo and OpenStreetMap) from the core LLM logic. By offloading external API calls, the MCP guarantees deterministic structural data fetching that the LLM later synthesises.
- **LLM Agent Backend (Port 8000):** Powered by LangChain and a local LLM via Ollama (e.g., `llama3.2:3b` or `mistral`). It intelligently routes the user intent, fires parallel asynchronous queries to the MCP server, and generates context-aware, structured travel itineraries in markdown.
- **Frontend (Port 5173):** A responsive, state-driven React interface that manages chat history and distinct rendering for raw text versus markdown structures.

### 3. Deployment Discussion
When transitioning ARIA to a production environment, the infrastructure will be modernized utilizing containerisation and orchestration:
- **Containerisation (Docker):** The Frontend, Agent Backend, and MCP Server will be individually containerised using Docker.
- **Orchestration (Kubernetes/Cloud Run):** 
  - The stateless **Frontend** and **MCP Server** can be deployed via managed serverless containers (e.g., Google Cloud Run or AWS Fargate) to scale elastically from zero to thousands of requests automatically.
  - The **LLM Backend** deployment depends on the LLM strategy. If maintaining a self-hosted local model, a Kubernetes cluster equipped with GPU-accelerated node pools scaling via KEDA (Kubernetes Event-driven Autoscaling) based on queue depth would be optimal.
- **Security:** In-cluster communication between the Agent Backend and the MCP Server would occur on a private subnet, preventing public internet access to the raw internal endpoints.

### 4. Documentation Philosophy
My documentation philosophy is built strictly on **Discoverability** and **Component Encapsulation** for the next developer inheriting the codebase:
- Code is aggressively modularised (routers vs. services) so a new developer can swap out an LLM provider or replace a data source without touching dependent code.
- Dependencies are ruthlessly managed natively via `requirements.txt` and `package.json`.
- The `.env.example` file acts as the ultimate truth for application configuration, requiring zero guesswork for environment bootstrapping.

---

## 🛠️ Code Repository & Setup Instructions

The repository is modularly structured to enable entirely independent development lifecycles for the client, agent, and server.

### Repository Structure
```text
AI_Builder/
├── mcp-server/          # FastAPI MCP wrapper (Fetches strictly real, open data)
│   ├── main.py
│   ├── routers/
│   ├── services/
│   │   ├── weather_service.py # Open-Meteo API integration
│   │   └── places_service.py  # Overpass API (OSM) integration
│   └── requirements.txt
│
├── agent-backend/       # LangChain agent + Ollama 
│   ├── main.py
│   ├── routers/
│   │   └── chat.py            # Ultra-fast parallel tool routing 
│   └── requirements.txt
│
└── frontend/            # React chat UI with Tailwind/Markdown integration
    ├── src/
    │   ├── App.jsx
    │   ├── index.css
    │   └── components/
    │       └── MessageBubble.jsx
    └── package.json
```

### Environment Requirements
**Prerequisites:** 
- Python 3.10+
- Node.js v18+
- [Ollama](https://ollama.com/) (Must be installed and running locally)

*Note: ARIA is designed to be 100% reliable with zero external API keys required, utilising Open-Meteo and Overpass API under the hood for free global traversal data.*

### Step 1: Start the Local LLM
Ensure Ollama is running, and pull a fast model.
```bash
ollama serve
ollama pull llama3.2:3b  # Or 'mistral'
```

### Step 2: Boot the MCP Context Server
Initiate the service responsible for gathering verifiable world data.
```bash
cd mcp-server
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001
```

### Step 3: Boot the Agent Backend
Initiate the orchestration layer.
```bash
cd agent-backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Create .env and set Ollama parameters
echo 'OLLAMA_MODEL=llama3.2:3b' > .env
echo 'OLLAMA_BASE_URL=http://localhost:11434' >> .env
echo 'MCP_SERVER_URL=http://localhost:8001' >> .env

uvicorn main:app --host 0.0.0.0 --port 8000
```

### Step 4: Boot the React Frontend
Initiate the aesthetic client UI.
```bash
cd frontend
npm install
npm run dev -- --port 5173
```
Visit **http://localhost:5173** to interact with ARIA!
