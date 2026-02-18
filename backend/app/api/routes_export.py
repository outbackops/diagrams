"""REST API routes for export and sharing.

Covers:
  - POST /export/{diagramId} (T071)
  - GET /share/{shareId} (T094)
"""

from __future__ import annotations

import base64
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from app.services.export_service import export_diagram, get_shared_diagram

router = APIRouter()


@router.post("/export/{diagram_id}", tags=["Export"])
async def export_diagram_endpoint(diagram_id: str, body: dict[str, Any]) -> dict[str, Any]:
    """Export diagram as image, code, or shareable link (T071)."""
    fmt = body.get("format", "png")
    if fmt not in ("png", "svg", "pdf", "py", "share"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {fmt}. Use: png, svg, pdf, py, share",
        )

    result = export_diagram(diagram_id, fmt)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    response: dict[str, Any] = {"format": result.get("format", fmt)}

    if "share_url" in result:
        response["share_url"] = result["share_url"]
        response["download_url"] = None
        response["content_base64"] = None
    elif "content_bytes" in result:
        content_b64 = base64.b64encode(result["content_bytes"]).decode("ascii")
        response["content_base64"] = content_b64
        response["download_url"] = None
        response["share_url"] = None
    else:
        response["download_url"] = None
        response["share_url"] = None
        response["content_base64"] = None

    return response


@router.get("/share/{share_id}", tags=["Export"], response_class=HTMLResponse)
async def get_shared_view(share_id: str) -> HTMLResponse:
    """Serve a read-only rendered diagram view (T094)."""
    shared = get_shared_diagram(share_id)
    if shared is None:
        raise HTTPException(status_code=404, detail="Shared diagram not found")

    # Simple read-only HTML view
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{shared['name']} - Diagram Agent</title>
    <style>
        body {{ font-family: sans-serif; margin: 2rem; background: #f8f9fa; }}
        h1 {{ color: #2d3436; font-size: 1.5rem; }}
        pre {{ background: white; padding: 1rem; border-radius: 8px; border: 1px solid #dee2e6;
               overflow-x: auto; font-size: 0.875rem; }}
        .meta {{ color: #868e96; font-size: 0.75rem; margin-top: 0.5rem; }}
    </style>
</head>
<body>
    <h1>{shared['name']}</h1>
    <pre><code>{shared['source_code']}</code></pre>
    <p class="meta">Shared from Diagram Agent</p>
</body>
</html>"""
    return HTMLResponse(content=html)
