"""Agent tools — wrap ai_agent, iac_parser, and export_service as callable
agent tools for the Foundry agent (T075).
"""

from __future__ import annotations

import json
from typing import Any

from app.models.iac import IaCFormat
from app.services.ai_agent import generate_diagram_from_prompt, refine_diagram_with_prompt
from app.services.code_executor import validate_code, execute_diagram_code
from app.services.diagram_service import diagram_service
from app.services.export_service import export_diagram
from app.services.iac_parser import parse_iac_content
from app.models.diagram import CreateDiagramRequest


async def tool_generate_diagram(prompt: str, providers: list[str] | None = None) -> dict[str, Any]:
    """Generate a diagram from a natural-language prompt."""
    ai_result = await generate_diagram_from_prompt(prompt, providers=providers)
    code = ai_result.get("code", "")

    if not code.strip():
        return {"error": "Failed to generate diagram code"}

    validation = validate_code(code)
    if not validation.valid:
        return {"error": "Generated code failed validation"}

    diagram = diagram_service.create(CreateDiagramRequest(name=prompt[:100]))
    diagram_service.update_from_generation(
        diagram.id, source_code=code, providers=validation.providers_used
    )

    # Execute to get rendered output
    exec_result = execute_diagram_code(code, output_format="png")

    return {
        "diagram_id": diagram.id,
        "source_code": code,
        "explanation": ai_result.get("explanation", ""),
        "rendered": exec_result.success,
    }


async def tool_refine_diagram(diagram_id: str, prompt: str) -> dict[str, Any]:
    """Refine an existing diagram."""
    diagram = diagram_service.get(diagram_id)
    if diagram is None:
        return {"error": "Diagram not found"}

    result = await refine_diagram_with_prompt(diagram.source_code, prompt)
    new_code = result.get("code", diagram.source_code)

    diagram_service.update_from_generation(diagram_id, source_code=new_code)

    return {
        "diagram_id": diagram_id,
        "source_code": new_code,
        "explanation": result.get("explanation", ""),
    }


async def tool_import_iac(content: str, format: str) -> dict[str, Any]:
    """Import IaC and generate a diagram."""
    iac_format = IaCFormat(format)
    result = await parse_iac_content(content, iac_format)
    code = result.get("code", "")

    if not code.strip():
        return {"error": "Failed to generate diagram from IaC"}

    diagram = diagram_service.create(CreateDiagramRequest(name=f"IaC Import - {format}"))
    diagram_service.update_from_generation(diagram.id, source_code=code)

    return {
        "diagram_id": diagram.id,
        "source_code": code,
        "explanation": result.get("explanation", ""),
    }


def tool_export_diagram(diagram_id: str, format: str) -> dict[str, Any]:
    """Export a diagram."""
    import base64

    result = export_diagram(diagram_id, format)
    if "error" in result:
        return result

    if "content_bytes" in result:
        result["content_base64"] = base64.b64encode(result.pop("content_bytes")).decode("ascii")

    return result
