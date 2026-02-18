"""REST API routes for IaC import.

Covers:
  - POST /import/file (T059)
  - POST /import/repository (T060)
  - POST /import/repository/confirm (T061)
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from app.models.diagram import CreateDiagramRequest
from app.models.iac import (
    ConfirmRepoImportRequest,
    IaCFormat,
    ImportRepoRequest,
    ImportResponse,
    RepoScanResponse,
)
from app.services.code_executor import validate_code
from app.services.diagram_service import diagram_service
from app.services.iac_parser import parse_iac_content

router = APIRouter()

# T095: Public-repo-only validation
BLOCKED_URL_PATTERNS = ["git@", "ssh://"]


def _validate_public_repo(url: str) -> None:
    """Reject non-public repository URLs (T095)."""
    for pattern in BLOCKED_URL_PATTERNS:
        if pattern in url:
            raise HTTPException(
                status_code=400,
                detail=f"Private repository URLs (SSH/git@) are not supported in MVP. "
                f"Please use a public HTTPS URL (e.g., https://github.com/user/repo).",
            )


@router.post("/import/file", tags=["Import"])
async def import_iac_file(
    file: UploadFile = File(...),
    format: str = Form(...),
) -> dict[str, Any]:
    """Upload an IaC file and generate a diagram (T059)."""
    try:
        iac_format = IaCFormat(format)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {format}. Use: terraform, cloudformation, bicep, kubernetes",
        )

    content = (await file.read()).decode("utf-8")
    if not content.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    result = await parse_iac_content(content, iac_format, file.filename)
    code = result.get("code", "")

    if not code.strip():
        raise HTTPException(status_code=400, detail="Failed to generate diagram from IaC")

    validation = validate_code(code)
    if not validation.valid:
        error_msgs = "; ".join(e.message for e in validation.errors)
        raise HTTPException(status_code=400, detail=f"Generated code invalid: {error_msgs}")

    diagram = diagram_service.create(
        CreateDiagramRequest(name=f"IaC Import - {file.filename or iac_format.value}")
    )
    diagram_service.update_from_generation(
        diagram.id, source_code=code, providers=validation.providers_used
    )

    updated = diagram_service.get(diagram.id)
    return ImportResponse(
        diagram=updated.model_dump(mode="json") if updated else {},
        parsed_resources=result.get("parsed_resources", []),
        unsupported_services=result.get("unsupported_services", []),
        explanation=result.get("explanation", ""),
    ).model_dump(mode="json")


@router.post("/import/repository", tags=["Import"])
async def import_repository(request: ImportRepoRequest) -> dict[str, Any]:
    """Scan a repository for IaC files (T060)."""
    _validate_public_repo(request.repo_url)

    # In MVP, return a stub scan result
    # Full implementation would clone/fetch repo and scan
    return RepoScanResponse(
        files=[],
        total_resources=0,
    ).model_dump()


@router.post("/import/repository/confirm", tags=["Import"])
async def confirm_repo_import(request: ConfirmRepoImportRequest) -> dict[str, Any]:
    """Generate diagram from selected repo files (T061)."""
    _validate_public_repo(request.repo_url)

    # Stub — would fetch files from repo and parse
    return ImportResponse(
        diagram={},
        parsed_resources=[],
        unsupported_services=[],
        explanation="Repository import requires files to be fetched first",
    ).model_dump(mode="json")
