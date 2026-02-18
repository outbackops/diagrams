# Technical Guide — Diagram Agent

This document covers architecture, development setup, and implementation details for contributors and operators.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite)                  │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ Monaco Editor │  │  React Flow  │  │ @hpcc-js/wasm      │    │
│  │ (code editor) │  │  (canvas)    │  │ (Graphviz layout)  │    │
│  └──────┬───────┘  └──────┬───────┘  └────────┬───────────┘    │
│         │                 │                    │                 │
│         └────────┬────────┘────────────────────┘                │
│                  │                                               │
│           Zustand Stores (diagramStore, codeStore, sessionStore) │
│                  │                                               │
│         ┌────────┴────────┐                                      │
│         │  apiClient.ts   │ REST + WebSocket                     │
│         └────────┬────────┘                                      │
└──────────────────┼──────────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │   Backend (FastAPI)  │
        │                      │
        │  ┌────────────────┐  │
        │  │  AI Agent       │  │  GPT-4.1 via Azure OpenAI
        │  │  (ai_agent.py)  │  │
        │  └───────┬────────┘  │
        │          │            │
        │  ┌───────┴────────┐  │
        │  │ Code Executor   │  │  AST validation → subprocess
        │  │ (code_executor) │  │  → Graphviz render
        │  └───────┬────────┘  │
        │          │            │
        │  ┌───────┴────────┐  │
        │  │ diagrams lib    │  │  Existing Python library
        │  │ + resources/    │  │  17+ providers, 800+ nodes
        │  └────────────────┘  │
        │                      │
        │  ┌────────────────┐  │
        │  │ Foundry Agent   │  │  Azure AI Foundry deployment
        │  │ (agent/)        │  │
        │  └────────────────┘  │
        └──────────────────────┘
```

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend | Python 3.11+, FastAPI | API server, AI orchestration, diagram execution |
| Frontend | TypeScript, React 18, Vite | SPA with interactive canvas and code editor |
| Canvas | React Flow (@xyflow/react) | Drag/connect/delete nodes with provider icons |
| Code Editor | Monaco Editor | Python syntax highlighting, inline errors, diff view |
| Layout Engine | @hpcc-js/wasm (client), Graphviz (server) | Client-side for <2s edits; server-side for export fidelity |
| AI Model | GPT-4.1 (primary), GPT-4.1-mini (fallback) | Code generation from natural language and IaC |
| State | Zustand | Reactive stores for graph model, code, and session |
| Styling | Tailwind CSS | Utility-first CSS |
| Deployment | Azure AI Foundry (Hosted Agent) | Docker container with Graphviz + diagrams library |
| Diagram Engine | [diagrams](https://diagrams.mingrammer.com/) v0.25.1 | Python library for diagram-as-code (vendored in repo) |

## Project Structure

```
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── main.py             # FastAPI entry point, middleware
│   │   ├── config.py           # Pydantic settings
│   │   ├── models/             # Pydantic data models
│   │   │   ├── diagram.py      # Diagram, DiagramVersion, LayoutMetadata
│   │   │   ├── prompt.py       # Prompt, PromptResponse
│   │   │   └── iac.py          # IaCSource, ParsedResource
│   │   ├── services/           # Business logic
│   │   │   ├── ai_agent.py     # AI orchestration (GPT-4.1)
│   │   │   ├── code_executor.py # AST validation + sandboxed execution
│   │   │   ├── node_registry.py # Introspect diagrams library
│   │   │   ├── diagram_service.py # CRUD + versioning
│   │   │   ├── iac_parser.py   # IaC → diagram via AI
│   │   │   ├── export_service.py # PNG/SVG/PDF/share
│   │   │   └── layout_service.py # Sidecar layout management
│   │   ├── api/                # Route handlers
│   │   │   ├── routes_diagram.py # CRUD, registry, validation, render
│   │   │   ├── routes_prompt.py  # Generate + refine
│   │   │   ├── routes_iac.py     # File upload + repo import
│   │   │   ├── routes_export.py  # Export + share
│   │   │   └── ws_sync.py       # WebSocket live sync
│   │   └── agent/              # Azure AI Foundry agent
│   │       ├── foundry_agent.py
│   │       └── tools.py
│   ├── Dockerfile              # Production container
│   ├── pyproject.toml
│   └── azure.yaml              # azd deployment config
│
├── frontend/                   # React + Vite SPA
│   ├── src/
│   │   ├── components/
│   │   │   ├── Canvas/         # React Flow: ProviderNode, ClusterGroup, EdgeConnection, DiagramCanvas
│   │   │   ├── Editor/         # Monaco: CodeEditor, DiffViewer, ErrorMarker
│   │   │   ├── Prompt/         # PromptInput, AIExplanation, ChatHistory
│   │   │   ├── Import/         # FileUpload, RepoConnect
│   │   │   ├── Export/         # ExportPanel
│   │   │   └── Layout/         # Toolbar, Sidebar, SplitPane
│   │   ├── stores/             # Zustand: diagramStore, codeStore, sessionStore
│   │   ├── services/           # apiClient, wsClient, codeParser, codeGenerator, graphvizLayout
│   │   ├── hooks/              # useBidirectionalSync, useAutoSave, useDiagramExport
│   │   └── types/              # TypeScript types (api.ts, diagram.ts)
│   ├── package.json
│   └── vite.config.ts
│
├── diagrams/                   # Core Python library (DO NOT hand-edit — use autogen.sh)
├── resources/                  # Provider icon assets (PNG, max 256×256)
├── config.py                   # autogen.sh configuration (providers, aliases)
├── autogen.sh                  # Generate node classes from icon assets
├── scripts/                    # Code generation scripts
├── templates/                  # Jinja templates for autogen
│
├── specs/                      # Feature specifications
│   └── 001-ai-diagram-agent/
│       ├── spec.md             # Requirements and user stories
│       ├── plan.md             # Technical plan
│       ├── tasks.md            # Task breakdown (97 tasks)
│       ├── research.md         # Technology decisions
│       ├── data-model.md       # Entity definitions
│       ├── quickstart.md       # Getting started guide
│       └── contracts/          # API contracts (OpenAPI + WebSocket)
│
├── .specify/                   # Speckit tooling
│   ├── memory/constitution.md  # Project constitution (6 principles)
│   ├── templates/
│   └── scripts/
│
└── .github/                    # GitHub agents and prompts
```

## Development Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

pip install -e ".[dev]"
cp .env.example .env        # Configure Azure AI credentials

# Run
uvicorn app.main:app --reload --port 8000

# Test
pytest
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env

# Copy provider icons for browser rendering
npm run copy-icons

# Run
npm run dev                 # http://localhost:5173

# Test
npm test
```

### Adding a New Provider

The `diagrams/` library node classes are **auto-generated** from icon assets:

1. Add icon files to `resources/<provider>/<category>/` (PNG, max 256×256px)
2. Update `config.py` with the new provider configuration
3. Run `./autogen.sh` to generate Python node classes
4. Commit both the icons and generated `diagrams/<provider>/` files

See [config.py](config.py) for provider configuration details.

## API Reference

### REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/diagrams` | List diagrams |
| `POST` | `/api/v1/diagrams` | Create diagram |
| `GET` | `/api/v1/diagrams/{id}` | Get diagram |
| `PUT` | `/api/v1/diagrams/{id}` | Update diagram |
| `DELETE` | `/api/v1/diagrams/{id}` | Delete diagram |
| `POST` | `/api/v1/diagrams/{id}/render` | Render to image |
| `GET` | `/api/v1/diagrams/{id}/versions` | Version history |
| `POST` | `/api/v1/prompts/generate` | Generate from prompt |
| `POST` | `/api/v1/prompts/refine` | Refine existing diagram |
| `POST` | `/api/v1/import/file` | Import IaC file |
| `POST` | `/api/v1/import/repository` | Scan repository |
| `POST` | `/api/v1/export/{id}` | Export diagram |
| `GET` | `/api/v1/share/{shareId}` | View shared diagram |
| `GET` | `/api/v1/registry/providers` | List providers |
| `GET` | `/api/v1/registry/providers/{p}/nodes` | List provider nodes |
| `GET` | `/api/v1/registry/search?q=` | Search nodes |
| `POST` | `/api/v1/validate` | Validate code |
| `GET` | `/health` | Health check |

Full OpenAPI spec: [specs/001-ai-diagram-agent/contracts/openapi.yaml](specs/001-ai-diagram-agent/contracts/openapi.yaml)

### WebSocket

Endpoint: `ws://{host}/api/v1/ws/{diagramId}`

| Client → Server | Server → Client |
|-----------------|-----------------|
| `code.update` | `render.result` |
| `canvas.update` | `code.sync` |
| `autosave.request` | `autosave.ack` |
| `ping` | `pong` |
| | `validation.error` |
| | `session.init` |
| | `error` |

Full protocol spec: [specs/001-ai-diagram-agent/contracts/websocket.md](specs/001-ai-diagram-agent/contracts/websocket.md)

## Code Execution Security

Diagram code is executed server-side through a three-layer sandbox:

1. **AST validation** — parse Python AST, whitelist `diagrams.*` imports only, reject `os`, `subprocess`, `eval`, `exec`, filesystem access, and network calls
2. **Subprocess isolation** — execute in a subprocess with CPU/memory limits, temporary working directory, restricted `PYTHONPATH`
3. **Container isolation** — Foundry hosted agent runs as non-root user in a minimal Docker container

## Constitution

The project is governed by 6 core principles defined in [.specify/memory/constitution.md](.specify/memory/constitution.md):

1. **Diagram Correctness** — rendered output must faithfully represent source code
2. **Architectural Fidelity** — icons and names must match official provider standards
3. **Code–Diagram Parity** — Python source is the single source of truth; round-trip sync is lossless
4. **Interactive Usability** — consistent layout across all providers; 4-level cluster nesting
5. **Extensibility** — new providers via `resources/` + `autogen.sh` only; stable public API
6. **Performance & Determinism** — byte-identical output across runs; AI decisions logged

## Deployment

### Azure AI Foundry (Hosted Agent)

```bash
# Build and push Docker image
docker build -t diagram-agent:latest -f backend/Dockerfile .
docker tag diagram-agent:latest <acr>.azurecr.io/diagram-agent:latest
docker push <acr>.azurecr.io/diagram-agent:latest

# Deploy with Azure Developer CLI
cd backend
azd up
```

### Local Docker

```bash
docker build -t diagram-agent:latest -f backend/Dockerfile .
docker run -p 8000:8000 --env-file backend/.env diagram-agent:latest
```

## License

[MIT](LICENSE)
