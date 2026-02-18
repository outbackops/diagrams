# Diagram Agent

**AI-powered architecture diagramming — from prompt to production-ready diagram in seconds.**

Diagram Agent generates, renders, and interactively edits cloud architecture diagrams using natural language. Describe your system in plain English, and the agent produces accurate, version-controlled diagram-as-code with correct provider icons for AWS, Azure, GCP, Kubernetes, and 13+ other providers.

## What It Does

| Capability | How It Works |
|-----------|-------------|
| **Generate from prompts** | Type _"Three-tier web app on AWS with ALB, ECS, and Aurora"_ and get a complete architecture diagram with correct service icons and relationships |
| **Live code editor** | View and edit the generated Python code — the diagram updates instantly as you type |
| **Interactive canvas** | Drag nodes, draw connections, rename labels, and group components — every visual change syncs back to code |
| **Import from IaC** | Upload Terraform, CloudFormation, Bicep, or Kubernetes files and auto-generate architecture diagrams |
| **Iterative refinement** | Follow up with _"add multi-region failover"_ or _"replace EC2 with ECS Fargate"_ — the AI modifies only what's needed |
| **Export & share** | Download as PNG, SVG, PDF, or self-contained Python code. Generate shareable links for read-only views |
| **Deploy as agent** | Package and deploy to Azure AI Foundry as an API-accessible agent |

## Key Principles

- **Code is the source of truth** — every diagram is valid Python using the [diagrams](https://diagrams.mingrammer.com/) library. No proprietary formats.
- **Bidirectional sync** — edit in code or on canvas; they always stay in sync.
- **AI transparency** — every AI decision includes an explanation and list of assumptions.
- **17+ providers** — AWS, Azure, GCP, Kubernetes, Alibaba Cloud, Oracle Cloud, IBM, OpenStack, Firebase, DigitalOcean, Elastic, Outscale, on-premises, generic, programming frameworks, SaaS, and C4 model.
- **Custom icons** — bring your own icons for services not in the library.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- [Graphviz](https://graphviz.org/download/) installed
- Azure AI Foundry project with GPT-4.1 deployment (for AI features)

### Run Locally

```bash
# Backend
cd backend
python -m venv .venv && .venv/Scripts/activate  # Windows
pip install -e ".[dev]"
cp .env.example .env  # Edit with your Azure AI credentials
uvicorn app.main:app --reload --port 8000

# Frontend (in a separate terminal)
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) and type your first prompt.

### Deploy to Azure AI Foundry

```bash
az login && azd auth login
azd up
```

## How It Works

```
User Prompt ──► AI Agent (GPT-4.1) ──► Python Code ──► AST Validation ──► Graphviz Render ──► Interactive Canvas
                     │                      │                                                        │
                     ▼                      ▼                                                        ▼
              Node Registry         Code Editor (Monaco)                                    React Flow Canvas
           (17+ providers,          (live syntax highlighting,                            (drag, connect, delete,
            800+ services)           inline error markers)                                  bidirectional sync)
```

## Example

**Prompt**: _"Serverless API on AWS with API Gateway, Lambda, DynamoDB, and CloudWatch"_

**Generated code**:
```python
from diagrams import Diagram, Cluster
from diagrams.aws.network import APIGateway
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.management import Cloudwatch

with Diagram("Serverless API", show=False, direction="LR"):
    api_gw = APIGateway("API Gateway")
    fn = Lambda("Handler")
    db = Dynamodb("Data Store")
    logs = Cloudwatch("Monitoring")

    api_gw >> fn >> db
    fn >> logs
```

## Export Formats

| Format | Description |
|--------|-------------|
| PNG | Raster image for documents and presentations |
| SVG | Vector image for web embedding |
| PDF | Print-ready document |
| Python (.py) | Self-contained executable — run with `diagrams` installed |
| Share link | Public read-only URL |

## Supported Providers

AWS · Azure · GCP · Kubernetes · Alibaba Cloud · Oracle Cloud · IBM · OpenStack · Firebase · DigitalOcean · Elastic · Outscale · On-Premises · Generic · Programming · SaaS · C4

## License

[MIT](LICENSE)
