# Research: AI Diagram Agent

**Feature**: `001-ai-diagram-agent`  
**Date**: 2026-02-18  
**Status**: Complete

## 1. Azure AI Foundry Agent Deployment

**Decision**: Deploy as a Hosted Agent — a custom Docker container running on Foundry Agent Service's managed infrastructure.

**Rationale**: The diagram agent requires custom runtime dependencies (the `diagrams` Python library + Graphviz binary), making it ineligible for the simpler "Prompt Agent" type (which only orchestrates model calls + built-in tools). Hosted agents allow arbitrary containerized code and expose it through the Foundry Responses API with autoscaling, identity management, and observability.

**How it works**:
1. Write agent code using the Microsoft Agent Framework
2. Wrap with the hosting adapter package (`azure-ai-agentserver-core` + `azure-ai-agentserver-agentframework`) which exposes the agent as a REST API on `localhost:8088`
3. Build a linux/amd64 Docker image containing the code, `diagrams`, Graphviz, and adapter
4. Push to Azure Container Registry
5. Deploy via `azd up` or the SDK (`azure-ai-projects>=2.0.0b3`)

**Key packages**:
| Package | Purpose |
|---|---|
| `azure-ai-projects>=2.0.0b3` | Foundry project client, agent management |
| `azure-ai-agentserver-core` | Hosting adapter core |
| `azure-ai-agentserver-agentframework` | Adapter for Microsoft Agent Framework |
| `azure-identity` | DefaultAzureCredential for auth |
| `agent-framework` | Microsoft Agent Framework |

**Alternatives considered**:
- Prompt Agent (Managed) — cannot run custom Python code or Graphviz
- Azure Container Apps / AKS — loses Foundry agent features (conversation, identity, evaluation)
- Azure Functions — cold-start latency, no persistent Graphviz runtime

## 2. Azure AI Foundry Model Selection

**Decision**: GPT-4.1 as primary model for code generation; GPT-4.1-mini as cost-effective fallback.

**Rationale**: GPT-4.1 has a 1M token context window, 32K max output tokens, structured outputs, and function calling. The `diagrams` library has 17+ providers with hundreds of node classes — feeding the full node registry as context requires a large context window. GPT-4.1 family is explicitly recommended for agent workloads by Azure documentation.

**Model selection strategy**:
1. Primary: GPT-4.1 — best balance of code quality, context size, and cost
2. Fallback: GPT-4.1-mini — for simpler single-provider diagrams or rate-limited scenarios
3. Consider: model-router — Foundry's built-in model that auto-selects based on prompt complexity
4. Future: GPT-5 family when GA

**Alternatives considered**:
- GPT-4o — only 128K context vs GPT-4.1's 1M
- Open-source models (Llama, DeepSeek) — code generation quality for specialized Python library unproven
- Codex-mini — overkill reasoning overhead

## 3. Foundry Publishing / Distribution

**Decision**: Agent Application publishing via Foundry + A2A (Agent-to-Agent) protocol for cross-platform interoperability.

**Rationale**: Publishing in Foundry promotes an agent to a managed Azure resource with a stable invocation URL, its own Entra Agent Identity, RBAC-controlled access, and OpenAI-compatible Responses API.

**Distribution channels**:
1. API endpoint — stable URL callable by any HTTP/OpenAI-compatible client
2. A2A Protocol (preview) — agent-to-agent communication via open protocol
3. Activity Protocol / Bot Service — connects to Teams, Slack, WebChat
4. Web app sharing — Foundry portal chat UI with role-based access
5. Version management — stable URL persists across agent version updates

**Alternatives considered**:
- Custom API Gateway (APIM) — adds rate limiting but increases complexity
- Direct container endpoint — loses Foundry identity/governance features
- Marketplace listing — not currently a Foundry feature

## 4. Interactive Canvas Library

**Decision**: React Flow (MIT licensed)

**Rationale**: Native support for custom node components (PNG icons), built-in drag/select/connect/delete interactions, nested sub flows for cluster grouping up to arbitrary depth, declarative graph model (not SVG manipulation) enabling bidirectional sync with code editor, and React-first integration. Handles 200+ nodes with viewport-based virtualization.

**Alternatives considered**:
- JointJS — strong runner-up but commercial license for full features
- GoJS — most feature-rich but commercial license (~$4K+)
- Cytoscape.js — designed for graph theory, weak nested cluster support
- D3.js — too low-level, 3-6 months extra work
- Fabric.js / Pixi.js — no graph/edge primitives

## 5. Code Editor

**Decision**: Monaco Editor

**Rationale**: Built-in Python syntax highlighting, first-class inline error marker API (`setModelMarkers`), `onDidChangeModelContent` for real-time editing callbacks, built-in diff editor for reviewing AI-suggested changes, VS Code familiarity for developer users, mature React wrapper (`@monaco-editor/react`).

**Alternatives considered**:
- CodeMirror 6 — smaller bundle but more manual setup for error markers, no built-in diff editor
- Ace Editor — maintenance mode, less modern

## 6. Graphviz in Browser

**Decision**: @hpcc-js/wasm (Graphviz compiled to WebAssembly)

**Rationale**: Runs entirely in-browser, supports JSON output format for structured layout data (node positions, edge splines, subgraph bounding boxes) without SVG parsing. ~4MB WASM binary, loads in <1 second. Supports all Graphviz layout engines (dot, neato, fdp, circo, twopi, osage).

**Key architectural insight**: Graphviz is used only for layout computation, not rendering. React Flow handles all rendering and interaction. Workflow: Python code → parse to DOT → @hpcc-js/wasm (JSON output) → extract positions → React Flow nodes/edges.

**Alternatives considered**:
- d3-graphviz — wraps @hpcc-js/wasm but adds D3 dependency and fights React Flow for DOM control
- Viz.js — older Emscripten port, larger bundle, less maintained

## 7. Frontend Framework

**Decision**: React + Vite

**Rationale**: Both React Flow and Monaco Editor are React-first. Complex state management for bidirectional sync is well-served by Zustand (bundled with React Flow). Largest ecosystem for UI components (Radix/shadcn) and AI integration (@ai-sdk for streaming).

**Alternatives considered**:
- Vue 3 — Vue Flow port lags behind React Flow in grouping features
- Svelte — no native React Flow wrapper, thinner Monaco support

## 8. Python Code Execution Sandboxing

**Decision**: Layered approach — AST validation + subprocess isolation within the hosted container.

**Layer 1 — AST validation (pre-execution)**:
- Parse generated Python code using Python's `ast` module
- Whitelist allowed imports: only `diagrams` and `diagrams.*` submodules
- Reject dangerous patterns: `os.system`, `subprocess`, `eval`, `exec`, `__import__`, file I/O outside temp dirs
- Validate that all referenced node classes exist in the library

**Layer 2 — Subprocess with restrictions (execution)**:
- Run validated code in subprocess with dropped privileges (non-root)
- Resource limits (ulimit for CPU time, memory)
- Temporary working directory cleaned after each execution
- Restricted PYTHONPATH

**Layer 3 — Container constraints (infrastructure)**:
- Foundry hosted agent container provides OS-level isolation
- Non-root user in Dockerfile
- Only required packages installed

**Alternatives considered**:
- Foundry Code Interpreter — cannot install Graphviz or custom libraries
- RestrictedPython — cannot sandbox Graphviz subprocess calls
- Docker-in-Docker — too complex, slow cold-start
- gVisor/Firecracker — not available in Foundry managed hosting

## 9. Backend Framework

**Decision**: FastAPI (Python)

**Rationale**: The `diagrams` library is Python, so the backend must be Python to import and execute diagram code directly. FastAPI provides async HTTP, WebSocket support (needed for live preview), automatic OpenAPI spec generation, and Pydantic model validation. Lightweight enough to run alongside the diagram rendering in the same container.

**Alternatives considered**:
- Flask — no native async, no WebSocket support without extensions
- Django — too heavyweight for an agent API service
- Node.js backend — would require IPC to invoke Python diagram code, adding latency and complexity

## 10. IaC Parsing Strategy

**Decision**: AI-assisted parsing using the LLM with structured output, not dedicated parsers per format.

**Rationale**: The four IaC formats (Terraform HCL, CloudFormation JSON/YAML, Bicep, K8s YAML) each have different syntaxes. Writing dedicated parsers for all four is high effort and brittle to version changes. Instead, send the IaC text to GPT-4.1 with a structured output schema that extracts resources, relationships, and groupings, then map to `diagrams` node classes. The LLM can handle format variations, infer relationships from references, and map provider-specific resource types to the library's node classes.

**Alternatives considered**:
- Dedicated parsers (python-hcl2, cfn-lint, etc.) — higher accuracy for individual formats but 4x implementation effort and ongoing maintenance
- Hybrid (dedicated parser for Terraform, LLM for others) — fragmented approach, consider if accuracy issues emerge
