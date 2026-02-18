# Feature Specification: AI Diagram Agent

**Feature Branch**: `001-ai-diagram-agent`  
**Created**: 2026-02-18  
**Status**: Draft  
**Input**: User description: "Build a web-based AI-powered architecture diagramming application that acts as a diagram agent. The application allows users to generate, view, edit, and maintain cloud and system architecture diagrams using diagram-as-code as the single source of truth."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Diagram from Natural Language (Priority: P1)

A user opens the web application and types a natural-language prompt such as "Three-tier web application on AWS with ALB, ECS, and Aurora PostgreSQL." The AI agent interprets the prompt, selects the correct provider nodes and relationships from the existing `diagrams` library, generates valid diagram-as-code Python, and renders an architecture diagram with correct service-specific icons. The user sees the rendered diagram and the corresponding code side by side.

**Why this priority**: This is the core value proposition — generating correct architecture diagrams from plain English. Without this, the application has no primary function.

**Independent Test**: Can be fully tested by submitting a natural-language prompt and verifying that (a) valid diagram-as-code Python is produced, (b) the rendered image matches the code, and (c) all referenced nodes exist in the `diagrams` library.

**Acceptance Scenarios**:

1. **Given** a user on the home screen, **When** they type "AWS Lambda behind API Gateway writing to DynamoDB" and submit, **Then** the system generates Python code using `diagrams.aws.compute.Lambda`, `diagrams.aws.network.APIGateway`, and `diagrams.aws.database.Dynamodb` with correct edges, and renders a matching diagram within 10 seconds.
2. **Given** a user submitting a prompt referencing services from multiple providers (e.g., AWS and GCP), **When** the prompt is processed, **Then** the system generates a multi-provider diagram using the correct provider-specific node classes and icons.
3. **Given** a user submitting an ambiguous or incomplete prompt, **When** the AI cannot confidently determine the architecture, **Then** it presents clarifying questions or lists its assumptions transparently before generating a diagram.
4. **Given** a user submitting a prompt referencing a service not in the `diagrams` library, **When** the AI processes it, **Then** the system informs the user which services are unsupported and suggests the closest available alternatives.

---

### User Story 2 - Live Code Editor with Instant Preview (Priority: P2)

A user views the generated diagram code in a live code editor pane. They modify the code — for example, adding a new node, changing a label, or altering edge connections — and the visual diagram updates immediately to reflect those changes. Syntax errors in the code are highlighted inline with descriptive messages.

**Why this priority**: Diagram-as-code is the single source of truth (Constitution Principle III). Users must be able to directly edit and verify the code. This is the foundation for all round-trip editing.

**Independent Test**: Can be fully tested by opening the code editor, making a code change (e.g., adding `ElastiCache` node), and verifying the rendered diagram updates within 2 seconds to include the new node with the correct icon.

**Acceptance Scenarios**:

1. **Given** a diagram is displayed with its code, **When** the user adds a new node line in the code editor, **Then** the diagram re-renders within 2 seconds showing the new node with the correct provider icon.
2. **Given** the user introduces a syntax error in the code editor, **When** the code is parsed, **Then** an inline error indicator highlights the offending line with a human-readable message, and the last valid diagram remains displayed.
3. **Given** the user removes an edge from the code, **When** the diagram re-renders, **Then** the corresponding visual connection disappears and no orphaned arrows remain.

---

### User Story 3 - Interactive Visual Canvas (Priority: P3)

A user interacts directly with the rendered diagram on an interactive canvas. They can drag nodes to reposition them, click a node to rename its label, draw a connection between two nodes, delete a component, or create/modify clusters (groupings). Every visual change is immediately reflected back into the code editor, maintaining bidirectional sync.

**Why this priority**: Visual editing makes the tool accessible to non-developers and speeds up iteration for all users. Bidirectional sync ensures code–diagram parity (Constitution Principle III).

**Independent Test**: Can be fully tested by dragging a node on the canvas, verifying the code updates, then editing the code and verifying the canvas updates — round-trip with no data loss.

**Acceptance Scenarios**:

1. **Given** a rendered diagram on the canvas, **When** the user drags a node to a new position, **Then** the layout metadata updates in a sidecar file (not in the diagram code) and the node stays in position on reload.
2. **Given** a rendered diagram, **When** the user right-clicks a node and selects "Rename," types a new label, and confirms, **Then** the `label` parameter in the code editor updates to match.
3. **Given** a rendered diagram, **When** the user draws a connection from Node A to Node B on the canvas, **Then** a new edge statement appears in the code using the `diagrams` API (e.g., `node_a >> node_b`), not raw DOT syntax.
4. **Given** a rendered diagram, **When** the user deletes a node on the canvas, **Then** the corresponding node declaration and all its edges are removed from the code.

---

### User Story 4 - Import from Infrastructure-as-Code / Repository (Priority: P4)

A user uploads or connects a repository containing infrastructure-as-code files (Terraform, CloudFormation, Bicep, or Kubernetes manifests). The AI agent analyzes the IaC to identify cloud resources, relationships, and groupings, then generates an accurate architecture diagram using diagram-as-code. The user can review the AI's interpretation before finalizing.

**Why this priority**: Generating diagrams from existing infrastructure closes the gap between deployed systems and documentation. This is high-value but depends on the core generation engine (P1) being functional first.

**Independent Test**: Can be fully tested by uploading a sample Terraform file defining an EC2 instance, VPC, and RDS database, and verifying the generated diagram includes all three resources with correct relationships and provider icons.

**Acceptance Scenarios**:

1. **Given** a user uploads a Terraform file with `aws_instance`, `aws_db_instance`, and `aws_vpc` resources, **When** the agent processes it, **Then** a diagram is generated showing EC2, RDS, and VPC cluster with correct edges inferred from resource references.
2. **Given** a user connects a GitHub repository, **When** the agent scans it, **Then** it identifies all IaC files, presents a summary of discovered resources, and lets the user confirm before generating the diagram.
3. **Given** a repository with IaC that references services not in the `diagrams` library, **When** the agent processes it, **Then** unsupported services are represented with `Custom` nodes and flagged to the user with an explanation.
4. **Given** a user uploads a Bicep file, **When** the agent processes it, **Then** it generates a diagram using `diagrams.azure.*` nodes matching the Azure resource types defined in the Bicep template.

---

### User Story 5 - Iterative Refinement via Follow-Up Prompts (Priority: P5)

A user has an existing diagram and wants to evolve it. They type a follow-up prompt such as "Add multi-region failover" or "Replace EC2 with ECS Fargate." The AI agent modifies the existing diagram code to incorporate the requested change, preserving all unaffected components. The user can review the diff before applying.

**Why this priority**: Iterative refinement is essential for real-world architecture work where designs evolve. It depends on the initial generation (P1) and code editing (P2) capabilities.

**Independent Test**: Can be fully tested by generating a diagram, then submitting a follow-up prompt that adds a component, and verifying the new component appears while all original components remain intact.

**Acceptance Scenarios**:

1. **Given** an existing diagram with an EC2 node, **When** the user prompts "Replace EC2 with ECS Fargate," **Then** the code replaces the `EC2` node with `ECS` (or the appropriate Fargate node), preserves all existing edges, and re-renders.
2. **Given** an existing single-region diagram, **When** the user prompts "Add multi-region failover with Route53," **Then** the code adds a second region cluster, Route53 node, and appropriate edges without duplicating the original region's internals.
3. **Given** a follow-up prompt that would result in an invalid architecture, **When** the AI detects the conflict, **Then** it explains the issue and suggests alternatives rather than silently generating a broken diagram.

---

### User Story 6 - Export and Share Diagrams (Priority: P6)

A user exports their completed diagram in multiple formats: as a Python code file, as an image (PNG, SVG, PDF), or as an embeddable artifact (iframe snippet, shareable link). Exported code is self-contained and executable with the `diagrams` library installed.

**Why this priority**: Export and sharing are essential for the diagram's utility beyond the application itself, but depend on diagram generation and editing being stable.

**Independent Test**: Can be fully tested by generating a diagram and exporting it as PNG, SVG, and Python code, then verifying the PNG/SVG match the displayed diagram and the Python code runs independently to produce the same output.

**Acceptance Scenarios**:

1. **Given** a completed diagram, **When** the user clicks "Export as PNG," **Then** a PNG file is downloaded that is visually identical to the on-screen diagram.
2. **Given** a completed diagram, **When** the user clicks "Export as Code," **Then** a `.py` file is downloaded that, when executed with `diagrams` installed, produces the same diagram.
3. **Given** a completed diagram, **When** the user clicks "Share," **Then** a shareable link or embed snippet is generated that renders the diagram in a read-only view.

---

### User Story 7 - Deploy as Azure Foundry Agent (Priority: P7)

The application is packaged and deployable as an Azure AI Foundry agent. Users can deploy the agent to Azure AI Foundry, expose it as an API endpoint, and publish it to other platforms via Foundry's distribution capabilities. The agent can receive prompts and return generated diagrams programmatically.

**Why this priority**: Deployment and distribution are the final mile. The agent must be functional (P1–P6) before it can be meaningfully deployed. This enables the "publish anywhere via Foundry" requirement.

**Independent Test**: Can be fully tested by deploying the agent to a Foundry endpoint, sending a prompt via the API, and verifying the response contains valid diagram code and a rendered image.

**Acceptance Scenarios**:

1. **Given** a configured Foundry project, **When** the operator runs the deployment command, **Then** the agent is deployed to Azure AI Foundry with a reachable API endpoint within 10 minutes.
2. **Given** a deployed Foundry agent, **When** an external client sends a prompt via the API, **Then** the agent returns a JSON response containing the generated diagram code and a URL or base64-encoded image of the rendered diagram.
3. **Given** a deployed Foundry agent, **When** the operator publishes it via Foundry, **Then** the agent is accessible on the target platform with the same capabilities.

---

### Edge Cases

- What happens when a user submits an empty or nonsensical prompt? The system returns a clear error message with example prompts and does not generate any diagram code.
- What happens when the uploaded IaC file is malformed or contains syntax errors? The system reports parsing errors with line numbers and does not attempt to generate a partial diagram from invalid input.
- What happens when a follow-up prompt contradicts the existing diagram (e.g., "Remove all nodes")? The system warns the user that the action would result in an empty diagram and asks for confirmation.
- What happens when the code editor and visual canvas are edited simultaneously? The last-saved edit wins; the system does not merge conflicting changes but shows a conflict notification.
- What happens when a diagram exceeds 200 nodes? The system displays a performance warning and offers to split the diagram into sub-diagrams by cluster.
- What happens when the user's session is interrupted (browser crash, network loss)? The system auto-saves diagram state at regular intervals and restores the last saved state on reconnection.
- What happens when the Foundry agent receives a request for an unsupported output format? The API returns a 400 error with a list of supported formats.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept natural-language prompts and generate valid diagram-as-code Python using the existing `diagrams` library as the generation engine.
- **FR-002**: System MUST render generated code into visual architecture diagrams with correct provider-specific icons sourced from `resources/`.
- **FR-003**: System MUST provide a live code editor where changes to diagram code produce immediate visual updates (< 2 second re-render for diagrams under 100 nodes).
- **FR-004**: System MUST provide an interactive visual canvas that supports drag-to-reposition, click-to-rename, draw-to-connect, and delete operations on diagram elements.
- **FR-005**: System MUST maintain bidirectional sync between the code editor and the visual canvas — changes in either MUST be reflected in the other without data loss.
- **FR-006**: System MUST map all visual canvas edits to valid `diagrams` Python API calls (e.g., `>>`, `<<`, `Edge()`, `Cluster()`) — never to raw Graphviz DOT manipulation.
- **FR-007**: System MUST store layout metadata (node positions from drag operations) in a sidecar file, separate from the diagram source code.
- **FR-008**: System MUST accept infrastructure-as-code files (Terraform, CloudFormation, Bicep, Kubernetes manifests) and generate corresponding architecture diagrams.
- **FR-009**: System MUST accept repository connections (e.g., GitHub URL) and scan for IaC files to generate diagrams from discovered infrastructure definitions.
- **FR-010**: System MUST support iterative refinement — follow-up prompts modify the existing diagram code, preserving unaffected components.
- **FR-011**: System MUST display the AI's assumptions, decisions, and reasoning transparently when generating or modifying diagrams.
- **FR-012**: System MUST export diagrams as Python code files, PNG, SVG, and PDF.
- **FR-013**: System MUST generate shareable links or embeddable artifacts for completed diagrams.
- **FR-014**: System MUST support all providers currently in the `diagrams` library (AWS, Azure, GCP, Kubernetes, Alibaba Cloud, Oracle Cloud, IBM, OpenStack, Firebase, DigitalOcean, Elastic, Outscale, on-premises, generic, programming, SaaS, C4).
- **FR-015**: System MUST support custom icon sets via `diagrams.custom.Custom` without requiring changes to the provider registry.
- **FR-016**: System MUST be deployable as an Azure AI Foundry agent with an API endpoint that accepts prompts and returns diagram code and rendered images.
- **FR-017**: System MUST expose Foundry publishing capabilities so the agent can be distributed to other platforms.
- **FR-018**: System MUST auto-save diagram state at regular intervals and restore it on session reconnection.
- **FR-019**: System MUST log all AI decision rationale (model used, prompt, parameters) for auditability and reproducibility.
- **FR-020**: System MUST enforce canonical best-practice layouts when generating diagrams from IaC or repositories (e.g., network tiers left-to-right, data flow top-to-bottom).

### Key Entities

- **Diagram**: A complete architecture diagram definition. Contains a name, provider scope, diagram-as-code source (Python), rendered output references, layout metadata, and version history.
- **Node**: A single architectural component (e.g., EC2, AKS, Cloud SQL). Has a provider, category, service name, icon reference, label, and position metadata.
- **Edge**: A directional or bidirectional relationship between two Nodes. Has a source node, target node, label, and style attributes.
- **Cluster**: A logical grouping of Nodes representing a boundary (e.g., VPC, region, availability zone). Can nest other Clusters up to four levels deep.
- **Prompt**: A user's natural-language instruction to generate or modify a diagram. Linked to a Diagram and tagged with the AI's interpretation and assumptions.
- **IaC Source**: An uploaded file or connected repository containing infrastructure definitions. Has a file type (Terraform, CloudFormation, Bicep, K8s), content, and a parsed resource inventory.
- **Export Artifact**: A generated output file (PNG, SVG, PDF, Python code) or shareable link derived from a Diagram.
- **Agent Deployment**: A configuration record for deploying the application as a Foundry agent. Contains the endpoint URL, deployment status, and API schema.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can generate a correct architecture diagram from a natural-language prompt in under 15 seconds for diagrams with up to 50 nodes.
- **SC-002**: 95% of generated diagrams use the correct provider-specific icons and node class names on the first attempt, as validated against the `diagrams` library's node registry.
- **SC-003**: Code-to-visual and visual-to-code sync completes within 2 seconds for diagrams under 100 nodes with zero data loss across 10 consecutive round-trip edits.
- **SC-004**: Users can import a Terraform/CloudFormation/Bicep file and receive an accurate architecture diagram within 30 seconds for files defining up to 100 resources.
- **SC-005**: Exported Python code files are self-contained and produce identical output when executed independently with the `diagrams` library installed.
- **SC-006**: The application supports all 17+ providers currently in the `diagrams` library without provider-specific UI code.
- **SC-007**: The Foundry agent API endpoint responds to prompt requests within 20 seconds and returns valid diagram code and a rendered image.
- **SC-008**: AI decision transparency: every generated or modified diagram includes a human-readable explanation of the AI's choices, visible to the user before they accept the result.
- **SC-009**: 90% of users can generate their first diagram within 3 minutes of opening the application, without reading documentation.
- **SC-010**: Diagrams with up to 200 nodes and 500 edges render without visual overlap, label collision, or missing icons.

## Assumptions

- The existing `diagrams` Python library (v0.25.1) in this repository will be used as the core diagram generation and rendering engine. No replacement or rewrite of the library is in scope.
- Graphviz is available as a runtime dependency for rendering, consistent with the library's existing requirements.
- Azure AI Foundry is the target deployment platform for the agent; specific Foundry SDK versions and model availability will be determined during planning.
- Users will authenticate via standard web authentication (session-based or OAuth2); the specific provider will be determined during planning.
- The web application frontend will communicate with a backend service that orchestrates AI model calls and `diagrams` library execution.
- Auto-save intervals default to every 30 seconds; the specific interval may be adjusted based on user feedback.
- IaC parsing covers the four major formats (Terraform HCL, CloudFormation JSON/YAML, Bicep, Kubernetes YAML); additional formats may be added as extensions.
