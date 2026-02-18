# Quickstart: AI Diagram Agent

**Feature**: `001-ai-diagram-agent`  
**Date**: 2026-02-18

## Prerequisites

- Python 3.11+
- Node.js 20+ and npm
- Graphviz installed (`brew install graphviz` on macOS, `apt install graphviz` on Ubuntu)
- An Azure AI Foundry project with a GPT-4.1 deployment (for AI features)

## 1. Clone and Setup

```bash
git clone https://github.com/outbackops/diagrams.git
cd diagrams
git checkout 001-ai-diagram-agent
```

## 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your Azure AI Foundry credentials:
#   AZURE_AI_PROJECT_CONNECTION_STRING=...
#   AZURE_OPENAI_DEPLOYMENT=gpt-4.1

# Run the backend
uvicorn app.main:app --reload --port 8000
```

The API is now available at `http://localhost:8000`. OpenAPI docs at `http://localhost:8000/docs`.

## 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env:
#   VITE_API_URL=http://localhost:8000
#   VITE_WS_URL=ws://localhost:8000

# Run the frontend
npm run dev
```

The application is now available at `http://localhost:5173`.

## 4. First Diagram

1. Open `http://localhost:5173` in your browser
2. In the prompt input, type: **"Three-tier web app on AWS with ALB, ECS, and Aurora PostgreSQL"**
3. Click **Generate**
4. The AI generates diagram-as-code Python and renders the architecture diagram
5. View the generated code in the left panel (Monaco Editor)
6. Interact with the diagram on the right panel (React Flow canvas)
7. Try editing the code — the diagram updates live
8. Try dragging a node — the layout sidecar updates (code stays clean)

## 5. Verify Round-Trip Sync

1. In the code editor, add a line: `elasticache = ElastiCache("Session Cache")`
2. The canvas adds a new ElastiCache node with the correct icon
3. On the canvas, draw an edge from the ECS node to the new ElastiCache node
4. The code editor shows a new `ecs >> elasticache` line
5. No data loss in either direction

## 6. Import from IaC

1. Click **Import** in the toolbar
2. Upload a Terraform file (`.tf`) or paste a GitHub repo URL
3. Review the discovered resources
4. Click **Generate Diagram**
5. The AI maps Terraform resources to `diagrams` node classes

## 7. Export

1. Click **Export** in the toolbar
2. Choose format: PNG, SVG, PDF, or Python Code
3. For Python Code: the exported `.py` file is self-contained and produces the same diagram when run with `python diagram.py` (with `diagrams` installed)

## 8. Deploy as Foundry Agent (optional)

```bash
cd backend

# Login to Azure
az login
azd auth login

# Deploy to Azure AI Foundry
azd up
```

The agent is now reachable via the Foundry Responses API endpoint shown in the deployment output.

## Running Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `graphviz` not found | Install Graphviz: `brew install graphviz` or `apt install graphviz` |
| WASM not loading in browser | Ensure you're using a modern browser (Chrome 90+, Firefox 90+, Safari 15+) |
| AI generation returns errors | Check `.env` has valid Azure AI Foundry credentials |
| Canvas icons not displaying | Run `npm run copy-icons` to copy provider icons to `public/icons/` |
| WebSocket disconnects | Check that the backend is running and `VITE_WS_URL` matches |
