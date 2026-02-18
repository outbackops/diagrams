# Implementation Plan: AI Diagram Agent

**Branch**: `001-ai-diagram-agent` | **Date**: 2026-02-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-ai-diagram-agent/spec.md`

## Summary

Build a web-based AI-powered architecture diagramming application (the "Diagram Agent") that generates, renders, and interactively edits cloud architecture diagrams using the existing `diagrams` Python library as the single source of truth. The application accepts natural-language prompts and IaC files, generates diagram-as-code Python, renders visual diagrams with correct provider icons, supports bidirectional code ↔ canvas editing, and deploys as an Azure AI Foundry agent. The backend is a FastAPI service wrapping the `diagrams` library with AI orchestration via GPT-4.1; the frontend is a React + Vite SPA with React Flow (interactive canvas) and Monaco Editor (live code editor), connected via WebSocket for real-time sync.

## Technical Context

**Language/Version**: Python 3.11+ (backend, diagrams library), TypeScript 5.x (frontend)  
**Primary Dependencies**: FastAPI, `diagrams` library (existing in repo), `graphviz`, `azure-ai-projects`, `agent-framework`; React 18, React Flow, Monaco Editor, @hpcc-js/wasm, Zustand, Vite  
**Storage**: File-based (diagram `.py` source + `.layout.json` sidecar); optional PostgreSQL/Cosmos DB for user sessions and diagram persistence in production  
**Testing**: pytest (backend), Vitest + React Testing Library (frontend)  
**Target Platform**: Linux container (backend), modern browsers (frontend), Azure AI Foundry (deployment)  
**Project Type**: Web application (frontend + backend)  
**Performance Goals**: <2s re-render for <100 nodes; <15s AI generation for <50 nodes; <30s IaC import for <100 resources  
**Constraints**: <200ms p95 for code↔canvas sync; diagrams with 200 nodes/500 edges must render without overlap; Graphviz WASM ~4MB initial load  
**Scale/Scope**: Single-user per session initially; 17+ providers with hundreds of node classes; 7 user stories across 4 major capability areas

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| **I. Diagram Correctness** | PASS | FR-001/FR-002: All rendered output derived from diagram-as-code; FR-006: no raw DOT manipulation from UI; AI-generated code validated via AST before execution |
| **II. Architectural Fidelity** | PASS | FR-014: All 17+ providers supported; node registry built from existing `resources/` hierarchy; icons sourced from official provider packs |
| **III. Code–Diagram Parity** | PASS | FR-005/FR-006/FR-007: Bidirectional sync with Python API mapping; layout metadata in sidecar file; `.py` source is authoritative |
| **IV. Interactive Usability** | PASS | FR-003/FR-004: Live editor + interactive canvas; consistent layout via Graphviz dot engine; cluster nesting supported via React Flow sub flows |
| **V. Extensibility** | PASS | FR-015: Custom nodes via `diagrams.custom.Custom`; new providers via existing `autogen.sh` flow; React Flow custom node components per provider |
| **VI. Performance & Determinism** | PASS | SC-001/SC-003/SC-010: Performance bounds defined; AI decisions logged (FR-019); Graphviz WASM produces deterministic layout |
| **Safety & Repository Integrity** | PASS | AST validation + subprocess sandboxing for code execution; no file access outside temp dirs; AI opt-in disclosure for IaC uploads |
| **Development Workflow** | PASS | pytest + Vitest; black/isort/pylint for Python; ESLint/Prettier for TypeScript |

## Project Structure

### Documentation (this feature)

```text
specs/001-ai-diagram-agent/
├── plan.md              # This file
├── research.md          # Phase 0 output — technology decisions
├── data-model.md        # Phase 1 output — entity definitions
├── quickstart.md        # Phase 1 output — getting started guide
├── contracts/           # Phase 1 output — API contracts
│   ├── openapi.yaml     # REST API specification
│   └── websocket.md     # WebSocket protocol specification
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
diagrams/                # Existing diagrams library (UNCHANGED)
├── __init__.py          # Diagram, Cluster, Node, Edge classes
├── cli.py               # Existing CLI
├── aws/                 # Provider modules (auto-generated)
├── azure/
├── gcp/
├── ...
└── custom/

resources/               # Existing icon assets (UNCHANGED)
├── aws/
├── azure/
└── ...

backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application entry point
│   ├── config.py        # Settings and environment configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── diagram.py   # Diagram, DiagramVersion data models
│   │   ├── prompt.py    # Prompt, AIDecisionLog data models
│   │   └── iac.py       # IaCSource, ParsedResource data models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_agent.py        # AI orchestration — prompt → code generation
│   │   ├── code_executor.py   # AST validation + sandboxed execution
│   │   ├── node_registry.py   # Introspect diagrams library for available nodes
│   │   ├── diagram_service.py # CRUD operations for diagrams
│   │   ├── iac_parser.py      # IaC file → resource extraction via AI
│   │   ├── export_service.py  # Export to PNG/SVG/PDF/code
│   │   └── layout_service.py  # Layout sidecar management
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes_diagram.py  # REST endpoints for diagrams
│   │   ├── routes_prompt.py   # REST endpoints for AI prompts
│   │   ├── routes_iac.py      # REST endpoints for IaC import
│   │   ├── routes_export.py   # REST endpoints for export
│   │   └── ws_sync.py         # WebSocket handler for live sync
│   └── agent/
│       ├── __init__.py
│       ├── foundry_agent.py   # Azure AI Foundry agent definition
│       └── tools.py           # Agent tools (generate, refine, import)
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── Dockerfile             # Foundry-deployable container
├── pyproject.toml
└── requirements.txt

frontend/
├── src/
│   ├── main.tsx           # Application entry point
│   ├── App.tsx            # Root component with layout
│   ├── components/
│   │   ├── Canvas/
│   │   │   ├── DiagramCanvas.tsx    # React Flow wrapper
│   │   │   ├── ProviderNode.tsx     # Custom node with provider icon
│   │   │   ├── ClusterGroup.tsx     # Nested cluster rendering
│   │   │   └── EdgeConnection.tsx   # Custom edge component
│   │   ├── Editor/
│   │   │   ├── CodeEditor.tsx       # Monaco Editor wrapper
│   │   │   ├── DiffViewer.tsx       # Diff view for AI changes
│   │   │   └── ErrorMarker.tsx      # Inline error display
│   │   ├── Prompt/
│   │   │   ├── PromptInput.tsx      # Natural language input
│   │   │   ├── AIExplanation.tsx    # AI decision transparency panel
│   │   │   └── ChatHistory.tsx      # Conversation thread for refinement
│   │   ├── Import/
│   │   │   ├── FileUpload.tsx       # IaC file upload
│   │   │   └── RepoConnect.tsx      # GitHub repository connection
│   │   ├── Export/
│   │   │   └── ExportPanel.tsx      # Export format selection
│   │   └── Layout/
│   │       ├── Toolbar.tsx          # Top toolbar
│   │       ├── Sidebar.tsx          # Side panel container
│   │       └── SplitPane.tsx        # Resizable code/canvas split
│   ├── stores/
│   │   ├── diagramStore.ts    # Zustand store — graph model (nodes, edges, clusters)
│   │   ├── codeStore.ts       # Zustand store — code editor state
│   │   └── sessionStore.ts    # Zustand store — user session, auto-save
│   ├── services/
│   │   ├── apiClient.ts       # REST API client
│   │   ├── wsClient.ts        # WebSocket client for live sync
│   │   ├── codeParser.ts      # Parse diagram Python code → graph model
│   │   ├── codeGenerator.ts   # Graph model → diagram Python code
│   │   └── graphvizLayout.ts  # @hpcc-js/wasm layout computation
│   ├── hooks/
│   │   ├── useBidirectionalSync.ts  # Code ↔ canvas sync orchestration
│   │   ├── useAutoSave.ts           # Periodic auto-save
│   │   └── useDiagramExport.ts      # Export operations
│   └── types/
│       ├── diagram.ts         # TypeScript type definitions
│       └── api.ts             # API request/response types
├── tests/
│   ├── components/
│   ├── services/
│   └── stores/
├── public/
│   └── icons/                 # Copied provider icons for browser rendering
├── index.html
├── vite.config.ts
├── tsconfig.json
├── package.json
└── tailwind.config.ts
```

**Structure Decision**: Web application structure (frontend + backend) selected because the feature requires both a Python backend (to run the `diagrams` library and orchestrate AI models) and a TypeScript frontend (interactive canvas, code editor, real-time sync). The existing `diagrams/` and `resources/` directories are consumed by the backend but not modified.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Web app structure (2 projects) | Backend must run Python `diagrams` library + Graphviz + AI orchestration; frontend needs rich interactive canvas + code editor in-browser | A single Python project with server-rendered templates cannot support React Flow, Monaco Editor, or sub-second bidirectional sync |
| Dual Graphviz (server + WASM) | Server-side Graphviz renders final export images (PNG/SVG/PDF) at full fidelity; client-side @hpcc-js/wasm computes layout positions for interactive editing | A single server-side Graphviz would add network round-trip latency on every edit, breaking the <2s re-render requirement |
