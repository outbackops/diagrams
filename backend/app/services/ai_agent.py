"""AI agent service — orchestrate prompt → code generation via GPT-4.1.

Includes:
- System prompt template with full node registry context (T031)
- Canonical layout rules (T090)
- prompt_hash computation (T091)
- Generation flow (T030)
- Refinement logic (T065 — stub for Phase 7)
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from app.config import settings
from app.services.node_registry import node_registry

# ──────────────────────────────────────────────
# Canonical layout rules (T090)
# ──────────────────────────────────────────────

CANONICAL_LAYOUT_RULES = """
## Canonical Layout Rules

When generating architecture diagrams, follow these best-practice layout conventions:

1. **Direction**: Use LR (left-to-right) for network/data flow diagrams, TB (top-to-bottom) for hierarchical/organizational diagrams.
2. **Network tiers**: Place load balancers on the left, compute/application tier in the center, databases/storage on the right (for LR layouts).
3. **VPCs and networks**: Wrap related resources in a Cluster representing the VPC or virtual network. Nest subnets as child clusters within the VPC cluster.
4. **Availability zones**: Represent AZs as nested clusters within the region cluster, placing redundant resources in parallel AZ clusters.
5. **Multi-region**: Place each region as a top-level cluster. Use a global services cluster (e.g., Route53, CloudFront) outside region clusters, connected to both regions.
6. **Data flow**: Arrows should follow the data flow direction. User → LB → App → DB is the canonical left-to-right flow.
7. **External services**: Place external/internet-facing components at the edges (leftmost for ingress, rightmost for egress).
8. **Grouping**: Group related services by function (compute cluster, storage cluster, monitoring cluster) rather than by provider category.
9. **Labels**: Use descriptive labels (e.g., "Web Server" not just "EC2"). Include the service name in the label for clarity.
10. **Edges**: Use >> for forward data flow, << for reverse, and - for bidirectional/non-directional connections.
"""

# ──────────────────────────────────────────────
# System prompt template
# ──────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """You are an expert cloud architect and diagram generator. You produce production-quality architecture diagrams as Python code using the `diagrams` library.

## Critical Rules

1. Generate ONLY valid Python code using the `diagrams` library API.
2. Use ONLY node classes from the registry below. Double-check every class name.
3. Every node MUST be inside a `with Diagram(...)` context manager.
4. Use `Cluster("label")` for logical groupings (VPCs, regions, subnets, AZs, tiers).
5. Use `>>` for forward data flow, `<<` for reverse, `-` for bidirectional.
6. ALWAYS set `show=False` in the Diagram constructor.
7. Import ONLY from `diagrams` and `diagrams.*` submodules. No os, sys, or other imports.
8. Give every node a descriptive snake_case variable name AND a descriptive label string.
9. Chain edges to show data flow: `user >> lb >> app >> db` (not individual pairs).

## Architecture Patterns — Use These

### Three-Tier Web Application
```python
from diagrams import Diagram, Cluster
from diagrams.aws.network import ELB, Route53
from diagrams.aws.compute import ECS
from diagrams.aws.database import RDS

with Diagram("Three-Tier Web App", show=False, direction="LR"):
    dns = Route53("DNS")
    with Cluster("VPC"):
        lb = ELB("Load Balancer")
        with Cluster("Application Tier"):
            app1 = ECS("App Server 1")
            app2 = ECS("App Server 2")
        with Cluster("Data Tier"):
            db = RDS("Primary DB")
    dns >> lb >> [app1, app2] >> db
```

### Serverless Event-Driven
```python
from diagrams import Diagram, Cluster
from diagrams.aws.network import APIGateway
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.integration import SQS, SNS

with Diagram("Serverless Architecture", show=False, direction="LR"):
    api = APIGateway("API Gateway")
    with Cluster("Processing"):
        fn = Lambda("Handler")
        queue = SQS("Task Queue")
        worker = Lambda("Worker")
    db = Dynamodb("Data Store")
    notify = SNS("Notifications")
    api >> fn >> queue >> worker >> db
    worker >> notify
```

### Microservices with Kubernetes
```python
from diagrams import Diagram, Cluster
from diagrams.k8s.network import Ingress, Service
from diagrams.k8s.compute import Deployment, Pod
from diagrams.k8s.storage import PV

with Diagram("K8s Microservices", show=False, direction="TB"):
    ingress = Ingress("Ingress Controller")
    with Cluster("Namespace: production"):
        with Cluster("Frontend"):
            fe_svc = Service("Frontend Svc")
            fe_deploy = Deployment("Frontend")
        with Cluster("Backend API"):
            api_svc = Service("API Svc")
            api_deploy = Deployment("API")
        with Cluster("Database"):
            db_svc = Service("DB Svc")
            db_deploy = Deployment("PostgreSQL")
            storage = PV("Persistent Volume")
    ingress >> fe_svc >> fe_deploy >> api_svc >> api_deploy >> db_svc >> db_deploy
    db_deploy - storage
```

{canonical_layout_rules}

## Available Node Classes

{node_registry}

## Output Format

Return a JSON object with:
- "code": Complete Python code as a string. Must be valid, runnable, and follow the patterns above.
- "explanation": Brief explanation of the architecture and why you chose these components.
- "assumptions": List of assumptions about the user's requirements.
- "warnings": List of unsupported services or potential issues (empty list if none).
- "providers": List of cloud providers used (e.g., ["aws"]).

Return ONLY the JSON object, no markdown code blocks or extra text.
"""


def compute_prompt_hash(
    user_text: str, model: str, parameters: dict[str, Any] | None = None
) -> str:
    """Compute SHA-256 hash of user_text + model + parameters for reproducibility (T091)."""
    payload = f"{user_text}|{model}|{json.dumps(parameters or {}, sort_keys=True)}"
    return hashlib.sha256(payload.encode()).hexdigest()


def build_system_prompt(providers_filter: list[str] | None = None) -> str:
    """Build the system prompt with node registry context.
    
    If providers_filter is given, only include those providers to reduce token usage.
    """
    if providers_filter:
        # Only include requested providers
        lines = []
        for p in providers_filter:
            nodes = node_registry.get_nodes_for_provider(p)
            if nodes:
                by_cat: dict[str, list[str]] = {}
                for n in nodes:
                    by_cat.setdefault(n.category, []).append(n.class_name)
                lines.append(f"\n## Provider: {p}")
                for cat, classes in sorted(by_cat.items()):
                    lines.append(f"  {cat}: {', '.join(sorted(classes))}")
        registry_text = "\n".join(lines)
    else:
        # Include top providers only to keep prompt under token limits
        top_providers = ["aws", "azure", "gcp", "k8s", "onprem"]
        lines = []
        for p in top_providers:
            nodes = node_registry.get_nodes_for_provider(p)
            if nodes:
                by_cat: dict[str, list[str]] = {}
                for n in nodes:
                    by_cat.setdefault(n.category, []).append(n.class_name)
                lines.append(f"\n## Provider: {p}")
                for cat, classes in sorted(by_cat.items()):
                    lines.append(f"  {cat}: {', '.join(sorted(classes))}")
        lines.append(f"\n## Other providers available: {', '.join(p for p in node_registry.providers if p not in top_providers)}")
        registry_text = "\n".join(lines)

    return SYSTEM_PROMPT_TEMPLATE.format(
        canonical_layout_rules=CANONICAL_LAYOUT_RULES,
        node_registry=registry_text,
    )


async def generate_diagram_from_prompt(
    user_text: str,
    providers: list[str] | None = None,
    theme: str = "neutral",
    direction: str = "LR",
) -> dict[str, Any]:
    """Generate diagram code from a natural-language prompt using GPT-4.1.

    Returns a dict with: code, explanation, assumptions, warnings, providers,
    model_used, prompt_hash, duration_ms
    """
    model = settings.azure_openai_deployment
    prompt_hash = compute_prompt_hash(user_text, model)
    system_prompt = build_system_prompt(providers_filter=providers)

    user_message = user_text
    if providers:
        user_message += f"\n\nRestrict to these providers: {', '.join(providers)}"
    user_message += f"\n\nUse theme='{theme}' and direction='{direction}'."

    start_time = time.time()

    try:
        from openai import AsyncAzureOpenAI
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider

        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default",
        )
        client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            azure_ad_token_provider=token_provider,
            api_version=settings.azure_openai_api_version,
        )
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        result = json.loads(content)

    except Exception as e:
        # Fallback: generate a simple placeholder diagram
        result = _generate_fallback(user_text, theme, direction)
        result["warnings"] = [f"AI service unavailable ({type(e).__name__}), using fallback generation"]

    duration_ms = int((time.time() - start_time) * 1000)

    return {
        "code": result.get("code", ""),
        "explanation": result.get("explanation", ""),
        "assumptions": result.get("assumptions", []),
        "warnings": result.get("warnings", []),
        "providers": result.get("providers", []),
        "model_used": model,
        "prompt_hash": prompt_hash,
        "duration_ms": duration_ms,
    }


async def refine_diagram_with_prompt(
    existing_code: str,
    user_text: str,
) -> dict[str, Any]:
    """Refine an existing diagram with a follow-up prompt (T065).

    Provides existing code as context, generates modified code,
    preserving unaffected components.
    """
    model = settings.azure_openai_deployment
    prompt_hash = compute_prompt_hash(user_text, model)
    system_prompt = build_system_prompt()

    user_message = f"""I have an existing diagram with this code:

```python
{existing_code}
```

Please modify this diagram based on the following instruction:
{user_text}

IMPORTANT:
- Preserve ALL existing components that are not affected by the change
- Only modify what is necessary to fulfill the instruction
- If the instruction would result in an invalid architecture, explain why and suggest alternatives
- Return the COMPLETE modified code, not just the changes

Return a JSON object with:
- "code": the complete modified Python code
- "explanation": what was changed and why
- "assumptions": any assumptions made
- "warnings": any potential issues
- "providers": list of providers used
"""

    start_time = time.time()

    try:
        from openai import AsyncAzureOpenAI
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider

        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default",
        )
        client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            azure_ad_token_provider=token_provider,
            api_version=settings.azure_openai_api_version,
        )
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content or "{}")
    except Exception:
        result = {
            "code": existing_code,
            "explanation": "AI service unavailable — code unchanged",
            "assumptions": [],
            "warnings": ["AI refinement unavailable, returning original code"],
            "providers": [],
        }

    duration_ms = int((time.time() - start_time) * 1000)

    return {
        "code": result.get("code", existing_code),
        "explanation": result.get("explanation", ""),
        "assumptions": result.get("assumptions", []),
        "warnings": result.get("warnings", []),
        "providers": result.get("providers", []),
        "model_used": model,
        "prompt_hash": prompt_hash,
        "duration_ms": duration_ms,
    }


def _generate_fallback(user_text: str, theme: str, direction: str) -> dict[str, Any]:
    """Generate a simple placeholder diagram when AI is unavailable."""
    code = f'''from diagrams import Diagram

with Diagram("{user_text[:50]}", show=False, direction="{direction}", theme="{theme}"):
    pass  # AI service unavailable — edit this code to add components
'''
    return {
        "code": code,
        "explanation": "Placeholder diagram created (AI service unavailable)",
        "assumptions": [],
        "warnings": ["AI generation unavailable — manual editing required"],
        "providers": [],
    }
