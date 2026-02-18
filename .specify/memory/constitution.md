<!--
  ============================================================
  Sync Impact Report
  ============================================================
  Version change: N/A → 1.0.0 (initial ratification)

  Modified principles: N/A (first version)

  Added sections:
    - Core Principles (6 principles)
    - Safety & Repository Integrity
    - Development Workflow & Quality Gates
    - Governance

  Removed sections: N/A

  Templates requiring updates:
    - .specify/templates/plan-template.md        ✅ compatible (no changes needed)
    - .specify/templates/spec-template.md         ✅ compatible (no changes needed)
    - .specify/templates/tasks-template.md        ✅ compatible (no changes needed)
    - .specify/templates/checklist-template.md    ✅ compatible (no changes needed)

  Follow-up TODOs: none
  ============================================================
-->

# Diagrams Constitution

## Core Principles

### I. Diagram Correctness

Every generated diagram MUST be a faithful visual representation of its
underlying diagram-as-code definition. No element—node, edge, cluster,
or label—may appear in the rendered output unless explicitly declared
in the source code.

- Rendered output MUST include every node and edge defined in source;
  no silent omissions.
- No phantom nodes, edges, or clusters may be injected by tooling,
  AI assistance, or rendering pipeline.
- Graphviz attribute overrides (e.g., `graph_attr`, `node_attr`,
  `edge_attr`) MUST propagate deterministically to the rendered SVG/PNG.
- When an error prevents correct rendering, the tool MUST fail loudly
  with a descriptive error rather than produce a partial or incorrect
  diagram.

**Rationale**: Diagrams is a specification tool—architects rely on its
output to document production systems. A silent deviation from source
code is a silent lie in documentation.

### II. Architectural Fidelity

Diagrams MUST maintain canonical architectural standards. Provider
iconography, naming conventions, and grouping hierarchies MUST reflect
the official terminology and visual identity of each cloud provider or
framework.

- Node class names MUST match official service names (e.g., `EC2`,
  not `ElasticCompute`; `AKS`, not `AzureKubernetes`).
- Icons MUST originate from official provider icon packs or be
  explicitly marked as community-contributed.
- Auto-generated node classes (`autogen.sh`) MUST preserve the
  provider → category → service hierarchy found in `resources/`.
- Deprecated provider services MUST be marked with deprecation
  warnings rather than silently removed, to avoid breaking existing
  diagrams.

**Rationale**: Users trust that a diagram produced by this library
accurately represents real cloud services. Incorrect naming or icons
undermine that trust and can mislead infrastructure decisions.

### III. Code–Diagram Parity

The diagram-as-code definition MUST be the single source of truth.
Any tooling that supports round-trip editing (UI ↔ code) MUST
guarantee that changes in one representation are losslessly reflected
in the other.

- A diagram defined in Python code and rendered, then re-imported
  from the visual output, MUST produce semantically identical code.
- UI-initiated modifications (drag, rename, reconnect) MUST map to
  valid Python API calls—never to raw Graphviz DOT manipulation
  that bypasses the `diagrams` API.
- Metadata not expressible in the Python API (e.g., free-form
  annotations added in a UI) MUST be stored in a sidecar file, not
  silently discarded or injected into the code.
- Serialization formats (DOT, JSON, intermediate representations)
  MUST be treated as derived artifacts; the `.py` source file is
  authoritative.

**Rationale**: Round-trip fidelity prevents "diagram drift," where
visual edits silently diverge from the codebase, creating a second
source of truth that conflicts with version-controlled code.

### IV. Interactive Usability

Diagrams MUST produce clear, navigable, and aesthetically consistent
output across all supported providers and frameworks. Layout, naming,
and iconography MUST be uniform so that multi-provider diagrams remain
readable.

- Default layout direction, spacing, and font choices MUST be
  consistent across providers unless the user explicitly overrides
  them.
- Node labels MUST default to the class name and be overridable via
  the `label` parameter—no silent truncation.
- Cluster (subgraph) nesting MUST render correctly up to at least
  four levels deep without visual overlap or label collision.
- CLI output (`diagrams` command) MUST support `--output-format`
  for at least PNG, SVG, and PDF without requiring additional
  user-installed tools beyond Graphviz.

**Rationale**: Architecture diagrams are communication artifacts.
Inconsistent styling or unreadable layouts force manual post-processing,
defeating the purpose of diagram-as-code.

### V. Extensibility

The architecture MUST support the addition of new providers, node
types, and output formats without modifying core library internals.

- Adding a new provider MUST require only: (a) placing icon assets
  in `resources/<provider>/<category>/`, and (b) running
  `autogen.sh` to generate node classes.
- Custom nodes (`diagrams.custom.Custom`) MUST accept any local or
  URL-based icon without requiring changes to the provider registry.
- The `Node`, `Edge`, `Cluster`, and `Diagram` base classes MUST
  remain stable public API; breaking changes require a major version
  bump.
- Third-party extensions (custom providers, exporters, renderers)
  MUST be supportable via subclassing or plugin registration without
  monkey-patching core modules.

**Rationale**: The library already supports 17+ providers. Growth
MUST NOT require invasive changes—each new provider should be a
self-contained addition.

### VI. Performance & Determinism

Diagram generation MUST produce deterministic output and complete
within predictable time and resource bounds.

- Given identical source code and identical Graphviz version, the
  rendered output MUST be byte-identical across runs and platforms.
- Node class auto-generation (`autogen.sh`) MUST be idempotent:
  running it twice with the same resource files MUST produce
  identical Python source.
- Rendering a diagram with up to 200 nodes and 500 edges MUST
  complete in under 30 seconds on commodity hardware (4-core CPU,
  8 GB RAM).
- AI-assisted features (code generation, layout suggestions) MUST
  log their decision rationale (model, prompt hash, parameters) so
  outputs are reproducible and auditable.

**Rationale**: Architecture diagrams are often generated in CI/CD
pipelines. Non-deterministic output causes spurious diffs; slow
generation blocks pipelines and developer workflows.

## Safety & Repository Integrity

Tooling and AI-assisted workflows MUST treat user repositories and
infrastructure code as read-sensitive assets. The following rules are
non-negotiable:

- The `diagrams` library MUST NOT read, write, or execute files
  outside the explicitly specified output directory.
- AI code-generation features MUST NOT transmit source code, file
  paths, or infrastructure topology to external services without
  explicit user opt-in and clear disclosure.
- Auto-generated files (node classes under `diagrams/`) MUST carry
  a header comment indicating they are generated and MUST NOT be
  hand-edited; `autogen.sh` is the sole mutation path.
- CLI commands MUST default to non-destructive behavior: overwriting
  an existing output file MUST require an explicit `--overwrite`
  flag or user confirmation.

## Development Workflow & Quality Gates

All contributions MUST pass the following gates before merge:

- **Lint**: `pylint` and `isort` MUST report zero errors on changed
  files.
- **Format**: Code MUST be formatted with `black`.
- **Tests**: `pytest` suite MUST pass. New provider nodes require at
  least one smoke-test diagram that renders without error.
- **Resource Integrity**: `autogen.sh` MUST be re-run after any
  change to `resources/`; the resulting diff in `diagrams/` MUST be
  committed alongside the resource change.
- **Icon Sizing**: All icon assets MUST fit within 256×256 pixels
  as specified in `CONTRIBUTING.md`.
- **Review**: PRs MUST include a rendered sample diagram demonstrating
  the change when the change affects visual output.

## Governance

This constitution is the authoritative governance document for the
Diagrams project. It supersedes ad-hoc conventions and informal
practices.

- **Amendment procedure**: Any change to this constitution MUST be
  proposed via PR, reviewed by at least one maintainer, and include
  a rationale. The Sync Impact Report (HTML comment at the top of
  this file) MUST be updated with every amendment.
- **Versioning policy**: The constitution follows semantic versioning.
  MAJOR for principle removals or incompatible redefinitions; MINOR
  for new principles or material expansions; PATCH for clarifications
  and typo fixes.
- **Compliance review**: Every feature plan (`plan.md`) MUST include
  a Constitution Check gate verifying alignment with these principles
  before implementation begins. Violations MUST be documented in the
  plan's Complexity Tracking table with justification.
- **Guidance file**: See `CONTRIBUTING.md` and `DEVELOPMENT.md` for
  runtime development guidance that operationalizes these principles.

**Version**: 1.0.0 | **Ratified**: 2025-02-18 | **Last Amended**: 2025-02-18
