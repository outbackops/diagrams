"""Export service — render diagram in requested format (PNG/SVG/PDF via Graphviz,
.py via code extraction). Share link generation (T070).
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from app.services.code_executor import execute_diagram_code
from app.services.diagram_service import diagram_service


# In-memory share store for MVP
_shared_diagrams: dict[str, dict[str, Any]] = {}


def export_diagram(
    diagram_id: str,
    fmt: str,
) -> dict[str, Any]:
    """Export a diagram in the requested format.

    Returns: { format, file_path, content_bytes, share_url }
    """
    diagram = diagram_service.get(diagram_id)
    if diagram is None:
        return {"error": "Diagram not found"}

    if fmt == "py":
        # Return the raw Python source code
        return {
            "format": "py",
            "content_bytes": diagram.source_code.encode("utf-8"),
            "filename": f"{diagram.name.replace(' ', '_').lower()}.py",
        }

    if fmt == "share":
        return create_share_link(diagram_id)

    # For image formats, execute the code
    result = execute_diagram_code(diagram.source_code, output_format=fmt)
    if not result.success:
        return {"error": result.error or "Export failed"}

    # Find the output file
    for fpath in result.output_files:
        if fpath.endswith(f".{fmt}"):
            with open(fpath, "rb") as f:
                content = f.read()
            return {
                "format": fmt,
                "content_bytes": content,
                "filename": f"{diagram.name.replace(' ', '_').lower()}.{fmt}",
            }

    return {"error": f"No {fmt} output produced"}


def create_share_link(diagram_id: str) -> dict[str, Any]:
    """Create a shareable link for a diagram (T070)."""
    diagram = diagram_service.get(diagram_id)
    if diagram is None:
        return {"error": "Diagram not found"}

    share_id = uuid.uuid4().hex[:12]
    _shared_diagrams[share_id] = {
        "diagram_id": diagram_id,
        "name": diagram.name,
        "source_code": diagram.source_code,
        "created_at": diagram.updated_at.isoformat(),
    }

    return {
        "format": "share",
        "share_url": f"/share/{share_id}",
        "share_id": share_id,
    }


def get_shared_diagram(share_id: str) -> dict[str, Any] | None:
    """Retrieve a shared diagram (T094)."""
    return _shared_diagrams.get(share_id)
