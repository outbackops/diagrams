"""REST API routes for diagrams CRUD, node registry, code validation, and rendering.

Covers:
  - GET/POST /diagrams
  - GET/PUT/DELETE /diagrams/{id}
  - GET /diagrams/{id}/versions
  - POST /diagrams/{id}/render
  - GET /registry/providers
  - GET /registry/providers/{provider}/nodes
  - GET /registry/search
  - POST /validate
"""

from __future__ import annotations

import base64
import os
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.models.diagram import CreateDiagramRequest, UpdateDiagramRequest
from app.services.code_executor import ExecutionResult, execute_diagram_code, validate_code
from app.services.diagram_service import diagram_service
from app.services.node_registry import node_registry

router = APIRouter()


# ──────────────────────────────────────────────
# Diagrams CRUD
# ──────────────────────────────────────────────


@router.get("/diagrams", tags=["Diagrams"])
async def list_diagrams() -> list[dict[str, Any]]:
    diagrams = diagram_service.list_all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "providers": d.providers,
            "version": d.version,
            "updated_at": d.updated_at.isoformat(),
        }
        for d in diagrams
    ]


@router.post("/diagrams", status_code=201, tags=["Diagrams"])
async def create_diagram(request: CreateDiagramRequest) -> dict[str, Any]:
    diagram = diagram_service.create(request)
    return diagram.model_dump(mode="json")


@router.get("/diagrams/{diagram_id}", tags=["Diagrams"])
async def get_diagram(diagram_id: str) -> dict[str, Any]:
    diagram = diagram_service.get(diagram_id)
    if diagram is None:
        raise HTTPException(status_code=404, detail="Diagram not found")
    return diagram.model_dump(mode="json")


@router.put("/diagrams/{diagram_id}", tags=["Diagrams"])
async def update_diagram(diagram_id: str, request: UpdateDiagramRequest) -> dict[str, Any]:
    diagram = diagram_service.update(diagram_id, request)
    if diagram is None:
        raise HTTPException(status_code=404, detail="Diagram not found")
    return diagram.model_dump(mode="json")


@router.delete("/diagrams/{diagram_id}", status_code=204, tags=["Diagrams"])
async def delete_diagram(diagram_id: str) -> None:
    if not diagram_service.delete(diagram_id):
        raise HTTPException(status_code=404, detail="Diagram not found")


@router.get("/diagrams/{diagram_id}/versions", tags=["Diagrams"])
async def list_diagram_versions(diagram_id: str) -> list[dict[str, Any]]:
    diagram = diagram_service.get(diagram_id)
    if diagram is None:
        raise HTTPException(status_code=404, detail="Diagram not found")
    versions = diagram_service.get_versions(diagram_id)
    return [
        {
            "id": v.id,
            "version": v.version,
            "change_summary": v.change_summary,
            "created_at": v.created_at.isoformat(),
        }
        for v in versions
    ]


@router.post("/diagrams/{diagram_id}/render", tags=["Diagrams"])
async def render_diagram(diagram_id: str, body: dict[str, Any] | None = None) -> Response:
    diagram = diagram_service.get(diagram_id)
    if diagram is None:
        raise HTTPException(status_code=404, detail="Diagram not found")
    if not diagram.source_code.strip():
        raise HTTPException(status_code=400, detail="Diagram has no source code")

    fmt = (body or {}).get("format", "svg")
    result: ExecutionResult = execute_diagram_code(diagram.source_code, output_format=fmt)

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error or "Render failed")

    # Find output file matching requested format
    for fpath in result.output_files:
        if fpath.endswith(f".{fmt}"):
            with open(fpath, "rb") as f:
                content = f.read()
            media_types = {
                "png": "image/png",
                "svg": "image/svg+xml",
                "pdf": "application/pdf",
            }
            return Response(content=content, media_type=media_types.get(fmt, "application/octet-stream"))

    raise HTTPException(status_code=500, detail=f"No {fmt} output produced")


# ──────────────────────────────────────────────
# Node Registry
# ──────────────────────────────────────────────


@router.get("/registry/providers", tags=["Registry"])
async def list_providers() -> list[str]:
    return node_registry.providers


@router.get("/registry/providers/{provider}/nodes", tags=["Registry"])
async def list_provider_nodes(provider: str) -> list[dict[str, Any]]:
    nodes = node_registry.get_nodes_for_provider(provider)
    if not nodes:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")
    return [
        {
            "provider": n.provider,
            "category": n.category,
            "class_name": n.class_name,
            "aliases": n.aliases,
            "icon_path": n.icon_path,
            "module_path": n.module_path,
        }
        for n in nodes
    ]


@router.get("/registry/search", tags=["Registry"])
async def search_nodes(q: str = Query(min_length=2)) -> list[dict[str, Any]]:
    results = node_registry.search(q)
    return [
        {
            "provider": n.provider,
            "category": n.category,
            "class_name": n.class_name,
            "aliases": n.aliases,
            "icon_path": n.icon_path,
            "module_path": n.module_path,
        }
        for n in results
    ]


# ──────────────────────────────────────────────
# Code Validation
# ──────────────────────────────────────────────


@router.post("/validate", tags=["Validation"])
async def validate_diagram_code(body: dict[str, Any]) -> dict[str, Any]:
    source_code = body.get("source_code", "")
    result = validate_code(source_code)
    return {
        "valid": result.valid,
        "errors": [
            {
                "line": e.line,
                "column": e.column,
                "message": e.message,
                "severity": e.severity,
            }
            for e in result.errors
        ],
        "node_count": result.node_count,
        "edge_count": result.edge_count,
        "providers_used": result.providers_used,
    }
