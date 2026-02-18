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

SYSTEM_PROMPT_TEMPLATE = """You are an expert cloud architecture diagram generator. You generate valid Python code using the `diagrams` library (https://diagrams.mingrammer.com/).

## Rules

1. Generate ONLY valid Python code that uses the `diagrams` library API.
2. Use ONLY node classes that exist in the library. The full registry is provided below.
3. Every node must be instantiated inside a `with Diagram(...)` context manager.
4. Use `Cluster` for logical groupings (VPCs, regions, subnets, availability zones).
5. Use `>>` for forward edges, `<<` for reverse edges, `-` for undirected edges.
6. Set `show=False` in the Diagram constructor.
7. Use `outformat="png"` (or the requested format).
8. Import only from `diagrams` and its submodules. No other imports.
9. Assign each node to a Python variable with a descriptive snake_case name.
10. Apply the canonical layout rules below.

{canonical_layout_rules}

## Available Node Classes

{node_registry}

## Output Format

Return a JSON object with these fields:
- "code": The complete Python code as a string
- "explanation": A brief explanation of architectural decisions made
- "assumptions": A list of assumptions made about the architecture
- "warnings": A list of any unsupported services or potential issues
- "providers": A list of cloud providers used (e.g., ["aws", "gcp"])

Return ONLY the JSON object, no markdown formatting.
"""


def compute_prompt_hash(
    user_text: str, model: str, parameters: dict[str, Any] | None = None
) -> str:
    """Compute SHA-256 hash of user_text + model + parameters for reproducibility (T091)."""
    payload = f"{user_text}|{model}|{json.dumps(parameters or {}, sort_keys=True)}"
    return hashlib.sha256(payload.encode()).hexdigest()


def build_system_prompt() -> str:
    """Build the full system prompt with node registry context."""
    registry_text = node_registry.get_registry_context()
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
    system_prompt = build_system_prompt()

    user_message = user_text
    if providers:
        user_message += f"\n\nRestrict to these providers: {', '.join(providers)}"
    user_message += f"\n\nUse theme='{theme}' and direction='{direction}'."

    start_time = time.time()

    try:
        from openai import AsyncAzureOpenAI

        # Attempt to use Azure OpenAI
        client = AsyncAzureOpenAI()
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
    """Refine an existing diagram with a follow-up prompt.

    Stub — full implementation in Phase 7 (T065).
    """
    model = settings.azure_openai_deployment
    prompt_hash = compute_prompt_hash(user_text, model)

    return {
        "code": existing_code,
        "explanation": "Refinement not yet implemented",
        "assumptions": [],
        "warnings": ["Refinement feature coming in Phase 7"],
        "providers": [],
        "diff": None,
        "model_used": model,
        "prompt_hash": prompt_hash,
        "duration_ms": 0,
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
