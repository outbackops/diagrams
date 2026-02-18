# Data Model: AI Diagram Agent

**Feature**: `001-ai-diagram-agent`  
**Date**: 2026-02-18  
**Source**: [spec.md](spec.md) Key Entities section

## Entities

### Diagram

Represents a complete architecture diagram definition. Central entity — all other entities relate to it.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Unique identifier |
| name | string | required, max 200 chars | Human-readable diagram name |
| source_code | text | required | Diagram-as-code Python source (the single source of truth) |
| dot_source | text | derived, nullable | Generated Graphviz DOT (derived artifact, not authoritative) |
| layout_metadata | JSON | nullable | Sidecar layout data — node positions from canvas drag operations (FR-007) |
| providers | string[] | derived from source_code | List of cloud providers used (e.g., ["aws", "gcp"]) |
| theme | string | default "neutral" | Graphviz theme (neutral, pastel, blues, greens, orange) |
| direction | string | default "LR" | Layout direction (TB, BT, LR, RL) |
| created_at | datetime | auto-set | Creation timestamp |
| updated_at | datetime | auto-updated | Last modification timestamp |
| version | integer | auto-increment on save | Version counter for change tracking |
| status | enum | "draft" \| "generated" \| "editing" | Current lifecycle state |

**Relationships**:
- Has many DiagramVersion (version history)
- Has many Prompt (generation/modification history)
- Has many ExportArtifact
- May have one IaCSource (if generated from IaC)

**State transitions**:
- `draft` → `generated` (after AI generates code)
- `generated` → `editing` (user modifies code or canvas)
- `editing` → `generated` (AI refines via follow-up prompt)
- Any state → `exported` (on export action, remains in previous state)

**Validation rules**:
- `source_code` must be parseable Python (validated via AST)
- `source_code` must import only from `diagrams` and `diagrams.*`
- `layout_metadata` must conform to the LayoutMetadata schema (see below)

---

### DiagramVersion

Immutable snapshot of a diagram at a point in time. Enables diffing and rollback.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Unique identifier |
| diagram_id | UUID | FK → Diagram.id, required | Parent diagram |
| version | integer | required | Version number (matches Diagram.version at snapshot time) |
| source_code | text | required | Python source code at this version |
| layout_metadata | JSON | nullable | Layout sidecar at this version |
| change_summary | string | nullable | What changed (AI-generated or user-provided) |
| created_at | datetime | auto-set | Snapshot timestamp |

**Validation rules**:
- `version` must be unique within a diagram_id
- `source_code` must be parseable Python

---

### Node (graph model — in-memory / frontend)

Represents a single architectural component within a diagram's graph model. This is the frontend runtime representation, not a persisted entity — the persisted form is the Python source code.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | string | unique within diagram | Node identifier (maps to Python variable name) |
| provider | string | required | Cloud provider (e.g., "aws", "azure", "gcp") |
| category | string | required | Service category (e.g., "compute", "database") |
| service | string | required | Service class name (e.g., "EC2", "Lambda", "AKS") |
| label | string | defaults to service name | Display label (maps to `label` parameter in Python) |
| icon_path | string | derived from provider/category/service | Path to icon asset in `resources/` |
| cluster_id | string | nullable | Parent cluster ID (null if top-level) |
| position | {x, y} | nullable | Canvas position from layout or drag (stored in sidecar) |

**Validation rules**:
- `provider` + `category` + `service` must resolve to a valid class in the `diagrams` library's node registry
- `label` must not be empty after trimming

---

### Edge (graph model — in-memory / frontend)

Represents a relationship between two nodes.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | string | unique within diagram | Edge identifier |
| source_node_id | string | required, FK → Node.id | Origin node |
| target_node_id | string | required, FK → Node.id | Destination node |
| direction | enum | "forward" \| "reverse" \| "both" \| "none" | Arrow direction (maps to `>>`, `<<`, `-`, Edge attrs) |
| label | string | nullable | Edge label text |
| style | string | nullable | Edge style (solid, dashed, dotted, bold) |
| color | string | nullable | Edge color |

**Validation rules**:
- `source_node_id` ≠ `target_node_id` (no self-loops unless explicitly supported)
- Both node IDs must exist in the diagram's node set

---

### Cluster (graph model — in-memory / frontend)

Represents a logical grouping of nodes (VPC, region, availability zone, etc.).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | string | unique within diagram | Cluster identifier |
| label | string | required | Display label (maps to Cluster `label` parameter) |
| parent_cluster_id | string | nullable | Parent cluster ID for nesting (null if top-level) |
| depth | integer | 0–3 | Nesting depth (max 4 levels per Constitution IV) |
| node_ids | string[] | subset of diagram nodes | Nodes contained in this cluster |
| child_cluster_ids | string[] | subset of diagram clusters | Nested child clusters |

**Validation rules**:
- `depth` must not exceed 3 (0-indexed, giving 4 levels)
- No circular nesting (a cluster cannot be its own ancestor)
- All `node_ids` must exist in the diagram's node set

---

### Prompt

A user's natural-language instruction and the AI's response.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Unique identifier |
| diagram_id | UUID | FK → Diagram.id, nullable | Associated diagram (null for initial generation) |
| user_text | text | required, max 5000 chars | User's natural language prompt |
| prompt_type | enum | "generate" \| "refine" \| "import" | Intent classification |
| ai_model | string | required | Model used (e.g., "gpt-4.1") |
| ai_response_code | text | nullable | Generated Python code (if successful) |
| ai_explanation | text | nullable | AI's reasoning and assumptions (FR-011) |
| ai_assumptions | JSON | nullable | Structured list of assumptions the AI made |
| prompt_hash | string | computed | SHA-256 of user_text + model + parameters (for reproducibility) |
| duration_ms | integer | nullable | Response time in milliseconds |
| created_at | datetime | auto-set | Timestamp |

**Validation rules**:
- `user_text` must not be empty after trimming
- `ai_response_code`, if present, must be parseable Python and import only from `diagrams`

---

### IaCSource

An uploaded infrastructure-as-code file or connected repository.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Unique identifier |
| diagram_id | UUID | FK → Diagram.id, nullable | Diagram generated from this source |
| source_type | enum | "file_upload" \| "repository" | How the IaC was provided |
| iac_format | enum | "terraform" \| "cloudformation" \| "bicep" \| "kubernetes" | IaC language |
| file_name | string | nullable | Original filename (for uploads) |
| repo_url | string | nullable | Repository URL (for connections) |
| content | text | required | Raw IaC file content |
| parsed_resources | JSON | nullable | Extracted resources after AI parsing |
| created_at | datetime | auto-set | Timestamp |

**Validation rules**:
- Either `file_name` or `repo_url` must be provided (based on `source_type`)
- `content` must not be empty
- `iac_format` must be one of the supported formats

---

### ExportArtifact

A generated output file from a diagram.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Unique identifier |
| diagram_id | UUID | FK → Diagram.id, required | Source diagram |
| format | enum | "png" \| "svg" \| "pdf" \| "py" | Export format |
| file_path | string | nullable | Server-side file path (temporary) |
| share_url | string | nullable | Public shareable URL (if shared) |
| file_size_bytes | integer | nullable | File size |
| created_at | datetime | auto-set | Timestamp |

---

### LayoutMetadata (embedded JSON schema)

Stored in `Diagram.layout_metadata` sidecar. Captures canvas positions from user drag operations, separate from diagram source code per Constitution III and FR-007.

```json
{
  "version": 1,
  "engine": "dot",
  "node_positions": {
    "<node_id>": { "x": 100.0, "y": 200.0, "pinned": true }
  },
  "cluster_bounds": {
    "<cluster_id>": { "x": 50.0, "y": 50.0, "width": 400.0, "height": 300.0 }
  },
  "viewport": {
    "zoom": 1.0,
    "pan_x": 0.0,
    "pan_y": 0.0
  }
}
```

- `pinned: true` means the user manually positioned this node (skip auto-layout for it)
- `viewport` stores the user's current zoom/pan state for session restoration

---

### NodeRegistryEntry (derived, read-only)

Introspected from the `diagrams` library at startup. Not persisted — built by scanning `diagrams/<provider>/<category>.py` modules.

| Field | Type | Description |
|-------|------|-------------|
| provider | string | Provider name (e.g., "aws") |
| category | string | Category name (e.g., "compute") |
| class_name | string | Python class name (e.g., "EC2") |
| aliases | string[] | Alternative names (e.g., ["ElasticComputeCloud"]) |
| icon_path | string | Relative path to icon in `resources/` |
| module_path | string | Full Python import path (e.g., "diagrams.aws.compute.EC2") |

## Entity Relationship Summary

```
Diagram 1──* DiagramVersion
Diagram 1──* Prompt
Diagram 1──* ExportArtifact
Diagram 1──0..1 IaCSource
Diagram ──contains──> Node* (in-memory graph model)
Diagram ──contains──> Edge* (in-memory graph model)
Diagram ──contains──> Cluster* (in-memory graph model)
Cluster ──contains──> Node* (membership)
Cluster ──contains──> Cluster* (nesting, max depth 3)
Edge ──connects──> Node (source) + Node (target)
NodeRegistryEntry (read-only, introspected from diagrams library)
```
