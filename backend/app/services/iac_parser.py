"""IaC parser service — send IaC content to GPT-4.1 with structured output schema,
extract resources and relationships, and map to diagrams node classes.

Includes canonical layout enforcement (T096).
"""

from __future__ import annotations

import json
import time
from typing import Any

from app.config import settings
from app.models.iac import IaCFormat, ParsedResource
from app.services.ai_agent import CANONICAL_LAYOUT_RULES, compute_prompt_hash
from app.services.node_registry import node_registry

IAC_PARSER_SYSTEM_PROMPT = f"""You are an infrastructure-as-code analyzer. Given IaC files
(Terraform, CloudFormation, Bicep, or Kubernetes YAML), extract all cloud resources,
their relationships, and logical groupings.

{CANONICAL_LAYOUT_RULES}

When generating diagram code from IaC, apply these layout rules to produce
well-structured, readable architecture diagrams.

## Output Format

Return a JSON object with:
- "resources": array of {{ "resource_type": "...", "resource_name": "...", "provider": "...", "relationships": ["other_resource_name", ...] }}
- "diagram_code": complete Python code using the diagrams library
- "explanation": explanation of architectural decisions
- "unsupported": list of resource types that couldn't be mapped

Return ONLY the JSON object, no markdown formatting.

## Available Node Classes
{{node_registry}}
"""


async def parse_iac_content(
    content: str,
    iac_format: IaCFormat,
    file_name: str | None = None,
) -> dict[str, Any]:
    """Parse IaC content using AI and generate diagram code."""
    model = settings.azure_openai_deployment
    prompt_hash = compute_prompt_hash(content[:500], model)

    registry_text = node_registry.get_registry_context()
    system_prompt = IAC_PARSER_SYSTEM_PROMPT.replace("{{node_registry}}", registry_text)

    user_message = f"""Analyze this {iac_format.value} file and generate an architecture diagram.

File: {file_name or "uploaded"}
Format: {iac_format.value}

Content:
```
{content[:10000]}
```

Generate a complete diagrams library Python code representing this infrastructure."""

    start_time = time.time()

    try:
        from openai import AsyncAzureOpenAI

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

        result = json.loads(response.choices[0].message.content or "{}")
    except Exception:
        result = _generate_iac_fallback(iac_format, file_name)

    duration_ms = int((time.time() - start_time) * 1000)

    # Map resources to ParsedResource objects
    parsed_resources = []
    for r in result.get("resources", []):
        mapped = _map_resource_to_node(r.get("resource_type", ""), r.get("provider", ""))
        parsed_resources.append(
            ParsedResource(
                resource_type=r.get("resource_type", ""),
                resource_name=r.get("resource_name", ""),
                mapped_node=mapped,
                relationships=r.get("relationships", []),
            )
        )

    return {
        "code": result.get("diagram_code", ""),
        "parsed_resources": parsed_resources,
        "unsupported_services": result.get("unsupported", []),
        "explanation": result.get("explanation", ""),
        "prompt_hash": prompt_hash,
        "duration_ms": duration_ms,
    }


def _map_resource_to_node(resource_type: str, provider: str = "") -> str | None:
    """Map an IaC resource type to a diagrams node class using the node registry (T058)."""
    # Common mappings
    type_lower = resource_type.lower().replace("_", "").replace("-", "")

    results = node_registry.search(resource_type.split("_")[-1] if "_" in resource_type else resource_type)
    if results:
        # Prefer same provider
        if provider:
            provider_matches = [r for r in results if r.provider == provider]
            if provider_matches:
                return provider_matches[0].module_path
        return results[0].module_path
    return None


def _generate_iac_fallback(iac_format: IaCFormat, file_name: str | None) -> dict:
    """Fallback when AI is unavailable."""
    return {
        "resources": [],
        "diagram_code": f'from diagrams import Diagram\n\nwith Diagram("IaC Import - {file_name or iac_format.value}", show=False):\n    pass  # AI unavailable\n',
        "explanation": "AI service unavailable — manual editing required",
        "unsupported": [],
    }
