"""REST API routes for AI prompts (generate and refine).

Covers:
  - POST /prompts/generate (T032-T033)
  - POST /prompts/refine (T064 — Phase 7)
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.models.diagram import CreateDiagramRequest, DiagramStatus
from app.models.prompt import GeneratePromptRequest, Prompt, PromptType, RefinePromptRequest
from app.services.ai_agent import generate_diagram_from_prompt, refine_diagram_with_prompt
from app.services.code_executor import execute_diagram_code, validate_code
from app.services.diagram_service import diagram_service

router = APIRouter()


@router.post("/prompts/generate", tags=["Prompts"])
async def generate_from_prompt(request: GeneratePromptRequest) -> dict[str, Any]:
    """Generate a new diagram from a natural-language prompt.

    Flow: prompt → AI → AST validation → sandboxed execution → render →
    return diagram + explanation (T033).
    """
    if not request.prompt.strip():
        raise HTTPException(
            status_code=400,
            detail="Prompt cannot be empty. Try something like: "
            "'Three-tier web app on AWS with ALB, ECS, and Aurora PostgreSQL'",
        )

    # Step 1: Call AI agent to generate code
    ai_result = await generate_diagram_from_prompt(
        user_text=request.prompt,
        providers=request.providers,
        theme=request.theme,
        direction=request.direction,
    )

    code = ai_result.get("code", "")
    if not code.strip():
        raise HTTPException(status_code=400, detail="AI failed to generate diagram code")

    # Step 2: AST validation
    validation = validate_code(code)
    if not validation.valid:
        error_msgs = "; ".join(e.message for e in validation.errors)
        raise HTTPException(
            status_code=400,
            detail=f"Generated code failed validation: {error_msgs}",
        )

    # Step 3: Create diagram record
    diagram = diagram_service.create(
        CreateDiagramRequest(name=request.prompt[:100], theme=request.theme, direction=request.direction)
    )

    # Step 4: Execute code for rendering
    exec_result = execute_diagram_code(code, output_format="png")

    # Step 5: Update diagram with generated code
    diagram_service.update_from_generation(
        diagram_id=diagram.id,
        source_code=code,
        dot_source=exec_result.dot_source if exec_result.success else None,
        providers=ai_result.get("providers", validation.providers_used),
    )

    # Step 6: Record the prompt
    prompt_record = Prompt(
        diagram_id=diagram.id,
        user_text=request.prompt,
        prompt_type=PromptType.GENERATE,
        ai_model=ai_result.get("model_used", ""),
        ai_response_code=code,
        ai_explanation=ai_result.get("explanation", ""),
        ai_assumptions=ai_result.get("assumptions", []),
        duration_ms=ai_result.get("duration_ms"),
    )
    prompt_record.compute_hash(ai_result.get("model_used", ""))

    # Reload diagram to get latest state
    updated_diagram = diagram_service.get(diagram.id)

    return {
        "diagram": updated_diagram.model_dump(mode="json") if updated_diagram else {},
        "explanation": ai_result.get("explanation", ""),
        "assumptions": ai_result.get("assumptions", []),
        "warnings": ai_result.get("warnings", []),
        "diff": None,
        "model_used": ai_result.get("model_used", ""),
        "prompt_hash": ai_result.get("prompt_hash", ""),
    }
