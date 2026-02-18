# Tasks: AI Diagram Agent

**Input**: Design documents from `/specs/001-ai-diagram-agent/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/openapi.yaml, contracts/websocket.md, quickstart.md

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Backend and frontend project initialization, dependency installation, and base configuration

- [ ] T001 Create backend project structure with pyproject.toml, requirements.txt, and .env.example in backend/
- [ ] T002 [P] Create frontend project with Vite + React + TypeScript scaffold in frontend/ (npm create vite@latest)
- [ ] T003 [P] Configure backend linting (pylint, isort, black) in backend/pyproject.toml
- [ ] T004 [P] Configure frontend linting (ESLint, Prettier) and Tailwind CSS in frontend/
- [ ] T005 [P] Create backend Dockerfile with Python 3.11, Graphviz, and diagrams library in backend/Dockerfile
- [ ] T006 [P] Create TypeScript type definitions for API request/response schemas in frontend/src/types/api.ts
- [ ] T007 [P] Create TypeScript type definitions for diagram graph model (Node, Edge, Cluster) in frontend/src/types/diagram.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008 Implement FastAPI application entry point with CORS, mount points, and health check in backend/app/main.py
- [ ] T009 Implement settings and environment configuration with Pydantic BaseSettings in backend/app/config.py
- [ ] T010 [P] Implement Diagram and DiagramVersion Pydantic models per data-model.md in backend/app/models/diagram.py
- [ ] T011 [P] Implement Prompt and AIDecisionLog Pydantic models per data-model.md in backend/app/models/prompt.py
- [ ] T012 [P] Implement IaCSource and ParsedResource Pydantic models per data-model.md in backend/app/models/iac.py
- [ ] T013 Implement node registry service that introspects the diagrams library to build provider→category→service map in backend/app/services/node_registry.py
- [ ] T014 Implement AST-based code validator — whitelist diagrams imports, reject unsafe patterns, validate node class references in backend/app/services/code_executor.py
- [ ] T015 Implement sandboxed code executor — subprocess with resource limits, temp directory, non-root user in backend/app/services/code_executor.py
- [ ] T016 Implement layout sidecar service — read/write LayoutMetadata JSON, merge pinned positions in backend/app/services/layout_service.py
- [ ] T017 Implement diagram CRUD service — create, read, update, delete, versioning in backend/app/services/diagram_service.py
- [ ] T018 [P] Implement REST API routes for diagrams CRUD per openapi.yaml (GET/POST /diagrams, GET/PUT/DELETE /diagrams/{id}, GET /diagrams/{id}/versions) in backend/app/api/routes_diagram.py
- [ ] T019 [P] Implement REST API routes for node registry (GET /registry/providers, GET /registry/providers/{provider}/nodes, GET /registry/search) in backend/app/api/routes_diagram.py
- [ ] T020 [P] Implement REST API route for code validation (POST /validate) in backend/app/api/routes_diagram.py
- [ ] T021 [P] Implement render endpoint (POST /diagrams/{id}/render) that executes code and returns PNG/SVG/PDF in backend/app/api/routes_diagram.py
- [ ] T022 [P] Create Zustand store for diagram graph model (nodes, edges, clusters, CRUD actions) in frontend/src/stores/diagramStore.ts
- [ ] T023 [P] Create Zustand store for code editor state (source code, dirty flag, error markers) in frontend/src/stores/codeStore.ts
- [ ] T024 [P] Create Zustand store for session state (diagram ID, auto-save timer, connection status) in frontend/src/stores/sessionStore.ts
- [ ] T025 [P] Implement REST API client with fetch wrapper for all backend endpoints in frontend/src/services/apiClient.ts
- [ ] T026 Implement Graphviz WASM layout service — load @hpcc-js/wasm, compute layout from DOT string, extract node positions in frontend/src/services/graphvizLayout.ts
- [ ] T027 [P] Implement application shell layout with Toolbar, Sidebar, and resizable SplitPane in frontend/src/components/Layout/Toolbar.tsx, Sidebar.tsx, SplitPane.tsx
- [ ] T028 Implement App.tsx root component wiring layout, stores, and routing in frontend/src/App.tsx
- [ ] T029 Copy provider icons from resources/ to frontend/public/icons/ via build script (add npm script "copy-icons" to frontend/package.json)

**Checkpoint**: Foundation ready — backend API running with CRUD + validation + rendering; frontend shell with stores and layout engine ready

---

## Phase 3: User Story 1 — Generate Diagram from Natural Language (Priority: P1) 🎯 MVP

**Goal**: Users type a natural-language prompt and receive a valid architecture diagram with correct provider icons and code

**Independent Test**: Submit "AWS Lambda behind API Gateway writing to DynamoDB" → verify generated Python code uses correct diagrams.aws classes, renders matching diagram within 15 seconds

### Implementation for User Story 1

- [ ] T030 [US1] Implement AI agent service — build system prompt with node registry context, call GPT-4.1, parse structured output in backend/app/services/ai_agent.py
- [ ] T031 [US1] Create system prompt template that includes full node registry, diagram code examples, and output format requirements in backend/app/services/ai_agent.py
- [ ] T032 [US1] Implement generate-from-prompt endpoint (POST /prompts/generate) per openapi.yaml in backend/app/api/routes_prompt.py
- [ ] T033 [US1] Wire generation flow: prompt → AI → AST validation → sandboxed execution → render → return diagram + explanation in backend/app/api/routes_prompt.py
- [ ] T034 [US1] Implement PromptInput component — text input with submit button, loading state, example prompts in frontend/src/components/Prompt/PromptInput.tsx
- [ ] T035 [US1] Implement AIExplanation component — display AI assumptions, reasoning, and warnings in frontend/src/components/Prompt/AIExplanation.tsx
- [ ] T036 [US1] Implement ProviderNode component — custom React Flow node rendering provider icon + label in frontend/src/components/Canvas/ProviderNode.tsx
- [ ] T037 [US1] Implement ClusterGroup component — nested container with themed background and label in frontend/src/components/Canvas/ClusterGroup.tsx
- [ ] T038 [US1] Implement EdgeConnection component — custom React Flow edge with direction arrows in frontend/src/components/Canvas/EdgeConnection.tsx
- [ ] T039 [US1] Implement DiagramCanvas component — React Flow wrapper rendering nodes/edges/clusters from diagramStore in frontend/src/components/Canvas/DiagramCanvas.tsx
- [ ] T040 [US1] Wire prompt submission flow: PromptInput → apiClient.generateFromPrompt → update diagramStore + codeStore → render on canvas in frontend/src/App.tsx

**Checkpoint**: User Story 1 fully functional — users can generate diagrams from natural language and see them rendered with icons

---

## Phase 4: User Story 2 — Live Code Editor with Instant Preview (Priority: P2)

**Goal**: Users edit diagram code in a live editor and see immediate visual updates within 2 seconds

**Independent Test**: Open code editor, add `elasticache = ElastiCache("Cache")` → verify canvas updates within 2 seconds with ElastiCache icon

### Implementation for User Story 2

- [ ] T041 [US2] Implement diagram Python code parser — extract nodes, edges, clusters from source code to build graph model in frontend/src/services/codeParser.ts
- [ ] T042 [US2] Implement CodeEditor component — Monaco Editor with Python syntax highlighting and onDidChangeModelContent callback in frontend/src/components/Editor/CodeEditor.tsx
- [ ] T043 [US2] Implement ErrorMarker component — display inline error indicators from validation.error WebSocket messages in frontend/src/components/Editor/ErrorMarker.tsx
- [ ] T044 [US2] Implement WebSocket client — connect to ws://.../ws/{diagramId}, handle all message types per websocket.md in frontend/src/services/wsClient.ts
- [ ] T045 [US2] Implement WebSocket server handler — accept connections, handle code.update, return render.result or validation.error per websocket.md in backend/app/api/ws_sync.py
- [ ] T046 [US2] Wire code→canvas flow: CodeEditor onChange (debounced 500ms) → wsClient.sendCodeUpdate → receive render.result → update diagramStore → canvas re-renders in frontend/src/hooks/useBidirectionalSync.ts

**Checkpoint**: User Story 2 fully functional — code edits produce live diagram updates with inline error feedback

---

## Phase 5: User Story 3 — Interactive Visual Canvas (Priority: P3)

**Goal**: Users interact with the canvas (drag, rename, connect, delete) and changes sync back to code

**Independent Test**: Drag a node, verify layout sidecar updates; rename a node, verify code updates; draw an edge, verify code shows `>>` operator; delete a node, verify code removes declaration and edges. Round-trip 10 times with no data loss.

### Implementation for User Story 3

- [ ] T047 [US3] Implement graph model → Python code generator — convert nodes/edges/clusters back to valid diagrams API code in frontend/src/services/codeGenerator.ts
- [ ] T048 [US3] Add drag-to-reposition handler to DiagramCanvas — on node drag end, send canvas.update(move_node) via WebSocket in frontend/src/components/Canvas/DiagramCanvas.tsx
- [ ] T049 [US3] Add rename handler — right-click context menu on nodes, send canvas.update(rename_node) via WebSocket in frontend/src/components/Canvas/DiagramCanvas.tsx
- [ ] T050 [US3] Add edge drawing handler — React Flow onConnect, send canvas.update(add_edge) via WebSocket in frontend/src/components/Canvas/DiagramCanvas.tsx
- [ ] T051 [US3] Add node/edge delete handler — keyboard Delete or context menu, send canvas.update(remove_node/remove_edge) via WebSocket in frontend/src/components/Canvas/DiagramCanvas.tsx
- [ ] T052 [US3] Implement canvas.update server handler — receive canvas actions, map to Python code mutations using diagrams API, return code.sync in backend/app/api/ws_sync.py
- [ ] T053 [US3] Implement code generation for canvas actions — add_node, remove_node, add_edge, remove_edge, rename_node → Python code transformations in backend/app/services/diagram_service.py
- [ ] T054 [US3] Wire canvas→code flow: canvas action → wsClient.sendCanvasUpdate → receive code.sync → update codeStore → Monaco editor updates in frontend/src/hooks/useBidirectionalSync.ts
- [ ] T055 [US3] Implement auto-save hook — periodic autosave.request every 30s via WebSocket, restore on reconnect in frontend/src/hooks/useAutoSave.ts
- [ ] T056 [US3] Implement autosave server handler — persist diagram + layout on autosave.request, return autosave.ack in backend/app/api/ws_sync.py

**Checkpoint**: User Story 3 fully functional — bidirectional sync between code and canvas with auto-save

---

## Phase 6: User Story 4 — Import from IaC / Repository (Priority: P4)

**Goal**: Users upload Terraform/CloudFormation/Bicep/K8s files or connect a repo and generate diagrams from infrastructure definitions

**Independent Test**: Upload a Terraform file with aws_instance, aws_db_instance, aws_vpc → verify diagram shows EC2, RDS, VPC cluster with correct edges

### Implementation for User Story 4

- [ ] T057 [US4] Implement IaC parser service — send IaC content to GPT-4.1 with structured output schema, extract resources and relationships in backend/app/services/iac_parser.py
- [ ] T058 [US4] Implement resource-to-node mapper — map IaC resource types to diagrams node classes using node registry in backend/app/services/iac_parser.py
- [ ] T059 [US4] Implement IaC file import endpoint (POST /import/file) per openapi.yaml — multipart upload, parse, generate diagram in backend/app/api/routes_iac.py
- [ ] T060 [US4] Implement repository scan endpoint (POST /import/repository) — clone/fetch repo, identify IaC files, return resource summary in backend/app/api/routes_iac.py
- [ ] T061 [US4] Implement repository confirm endpoint (POST /import/repository/confirm) — generate diagram from selected files in backend/app/api/routes_iac.py
- [ ] T062 [US4] Implement FileUpload component — drag-and-drop area, format detection, upload to /import/file in frontend/src/components/Import/FileUpload.tsx
- [ ] T063 [US4] Implement RepoConnect component — URL input, branch selection, file list with checkboxes, confirm button in frontend/src/components/Import/RepoConnect.tsx

**Checkpoint**: User Story 4 fully functional — IaC files and repos generate accurate architecture diagrams

---

## Phase 7: User Story 5 — Iterative Refinement via Follow-Up Prompts (Priority: P5)

**Goal**: Users refine existing diagrams with follow-up prompts, preserving unaffected components

**Independent Test**: Generate an EC2 diagram, prompt "Replace EC2 with ECS Fargate" → verify EC2 replaced, all other nodes/edges preserved, diff shown

### Implementation for User Story 5

- [ ] T064 [US5] Implement refine-with-prompt endpoint (POST /prompts/refine) — send existing code + prompt to AI, return modified code + diff in backend/app/api/routes_prompt.py
- [ ] T065 [US5] Implement AI refinement logic — provide existing code as context, generate only the changes, produce unified diff in backend/app/services/ai_agent.py
- [ ] T066 [US5] Implement ChatHistory component — display conversation thread of prompts and AI responses in frontend/src/components/Prompt/ChatHistory.tsx
- [ ] T067 [US5] Implement DiffViewer component — Monaco diff editor showing before/after with accept/reject buttons in frontend/src/components/Editor/DiffViewer.tsx
- [ ] T068 [US5] Wire refinement flow: follow-up prompt → apiClient.refineWithPrompt → show diff in DiffViewer → on accept, update diagramStore + codeStore in frontend/src/App.tsx

**Checkpoint**: User Story 5 fully functional — diagrams evolve iteratively with preserving existing components

---

## Phase 8: User Story 6 — Export and Share Diagrams (Priority: P6)

**Goal**: Users export diagrams as PNG, SVG, PDF, Python code, or shareable links

**Independent Test**: Generate a diagram, export as PNG/SVG/Code → verify PNG/SVG match display, exported .py runs independently

### Implementation for User Story 6

- [ ] T069 [US6] Implement export service — render diagram in requested format (PNG/SVG/PDF via Graphviz, .py via code extraction) in backend/app/services/export_service.py
- [ ] T070 [US6] Implement share link generation — persist diagram snapshot, generate public URL with read-only view in backend/app/services/export_service.py
- [ ] T071 [US6] Implement export endpoint (POST /export/{diagramId}) per openapi.yaml in backend/app/api/routes_export.py
- [ ] T072 [US6] Implement ExportPanel component — format selector (PNG/SVG/PDF/Code/Share), download trigger in frontend/src/components/Export/ExportPanel.tsx
- [ ] T073 [US6] Implement useDiagramExport hook — call export endpoint, handle download and share URL copy in frontend/src/hooks/useDiagramExport.ts

**Checkpoint**: User Story 6 fully functional — diagrams exportable in all formats and shareable via links

---

## Phase 9: User Story 7 — Deploy as Azure Foundry Agent (Priority: P7)

**Goal**: Application packaged and deployable as an Azure AI Foundry agent with API endpoint

**Independent Test**: Deploy agent to Foundry endpoint, send prompt via API → verify response contains valid diagram code and rendered image

### Implementation for User Story 7

- [ ] T074 [US7] Implement Foundry agent definition — define agent with generate/refine/import tools using Microsoft Agent Framework in backend/app/agent/foundry_agent.py
- [ ] T075 [US7] Implement agent tools — wrap ai_agent, iac_parser, and export_service as callable agent tools in backend/app/agent/tools.py
- [ ] T076 [US7] Configure hosting adapter — add azure-ai-agentserver-core + agentframework dependencies, expose on localhost:8088 in backend/app/agent/foundry_agent.py
- [ ] T077 [US7] Update backend Dockerfile for Foundry deployment — add hosting adapter entrypoint, non-root user, ACR push instructions in backend/Dockerfile
- [ ] T078 [US7] Create Azure Developer CLI configuration (azure.yaml) for azd up deployment in backend/azure.yaml
- [ ] T079 [US7] Create Foundry agent publishing script — register agent application, configure Entra identity, publish endpoint in backend/scripts/publish_agent.py

**Checkpoint**: User Story 7 fully functional — agent deployed to Azure AI Foundry and reachable via API

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T080 [P] Add error handling middleware with standardized Error response format in backend/app/main.py
- [ ] T081 [P] Add request logging and AI decision audit logging (model, prompt_hash, parameters) in backend/app/main.py
- [ ] T082 [P] Add performance warning when diagram exceeds 200 nodes in both backend (render endpoint) and frontend (diagramStore)
- [ ] T083 [P] Add conflict detection when code editor and canvas are edited simultaneously in frontend/src/hooks/useBidirectionalSync.ts
- [ ] T084 [P] Add session restoration — reconnect WebSocket and restore last auto-saved state on page reload in frontend/src/hooks/useAutoSave.ts
- [ ] T085 [P] Add empty/nonsensical prompt validation with example prompts in backend/app/api/routes_prompt.py
- [ ] T086 Code cleanup — remove unused imports, ensure consistent error handling patterns across all backend routes
- [ ] T087 [P] Update quickstart.md with final setup instructions and troubleshooting after implementation in specs/001-ai-diagram-agent/quickstart.md
- [ ] T088 Run quickstart.md validation — follow all steps end-to-end and verify they produce the expected results

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–9)**: All depend on Foundational phase completion
  - US1 (Phase 3): Can start after Foundational — no dependencies on other stories
  - US2 (Phase 4): Can start after Foundational — benefits from US1 for test data but not strictly required
  - US3 (Phase 5): Depends on US2 (code parser and WebSocket) — bidirectional sync needs code→canvas first
  - US4 (Phase 6): Can start after Foundational — parallel with US2/US3
  - US5 (Phase 7): Depends on US1 (AI generation) and US2 (code editing) — needs existing diagram + code context
  - US6 (Phase 8): Can start after Foundational — parallel with other stories
  - US7 (Phase 9): Depends on US1 (core generation) — agent wraps existing services
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — Independent of US1; uses same renderer but different entry point
- **User Story 3 (P3)**: Depends on US2 — needs codeParser.ts, wsClient.ts, and the WebSocket server handler
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) — Independent of US1-US3; shares AI service
- **User Story 5 (P5)**: Depends on US1 (AI agent service) and US2 (code editor) — refinement needs generation + editing
- **User Story 6 (P6)**: Can start after Foundational (Phase 2) — Only needs diagram CRUD and rendering
- **User Story 7 (P7)**: Depends on US1 (AI agent service) — wraps generation as agent tool

### Within Each User Story

- Models before services
- Services before API routes/endpoints
- Backend before frontend (frontend needs API to call)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- After Foundational: US1, US2, US4, US6 can all start in parallel
- After US2: US3 can start
- After US1 + US2: US5 can start
- After US1: US7 can start
- Frontend and backend tasks within a story are sequential (backend first)

---

## Parallel Example: After Foundational Phase

```bash
# Stream 1: User Story 1 (AI Generation — MVP)
T030 → T031 → T032 → T033 → T034 → T035 → T036,T037,T038 → T039 → T040

# Stream 2: User Story 2 (Code Editor — can start in parallel with US1)
T041 → T042,T043 → T044,T045 → T046

# Stream 3: User Story 4 (IaC Import — independent of US1/US2)
T057 → T058 → T059,T060,T061 → T062,T063

# Stream 4: User Story 6 (Export — independent)
T069 → T070 → T071 → T072 → T073

# After Stream 2 completes:
# Stream 5: User Story 3 (Canvas Interactions — needs US2 WebSocket)
T047 → T048,T049,T050,T051 → T052 → T053 → T054 → T055,T056

# After Stream 1 + Stream 2 complete:
# Stream 6: User Story 5 (Refinement — needs US1 AI + US2 editor)
T064 → T065 → T066,T067 → T068

# After Stream 1 completes:
# Stream 7: User Story 7 (Foundry Agent — needs US1 AI service)
T074 → T075 → T076 → T077 → T078 → T079
```

---

## Implementation Strategy

**MVP**: User Story 1 (Phase 3) — AI-generated diagrams from natural language. Delivers the core value proposition. Testable independently.

**Incremental delivery**:
1. Phase 1–2: Foundation (both projects scaffolded, API running, stores ready)
2. Phase 3: MVP — generate diagrams from prompts
3. Phase 4: Code editing with live preview
4. Phase 5: Full bidirectional sync (canvas ↔ code)
5. Phase 6–8: Import, refinement, export (can parallelize)
6. Phase 9: Foundry agent deployment
7. Phase 10: Polish

**Total tasks**: 88
