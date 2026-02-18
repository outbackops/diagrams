"""WebSocket handler for live sync per contracts/websocket.md.

Handles:
  - code.update → validate + render → render.result | validation.error
  - canvas.update → code mutation → code.sync
  - autosave.request → persist → autosave.ack
  - ping → pong
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.code_executor import validate_code, execute_diagram_code
from app.services.diagram_service import diagram_service
from app.models.diagram import UpdateDiagramRequest, LayoutMetadata

router = APIRouter()
logger = logging.getLogger(__name__)


def _build_graph_model_from_exec(exec_result: Any) -> dict:
    """Build a simplified graph model from execution results.
    Full parsing happens on the frontend via codeParser.ts."""
    return {"nodes": [], "edges": [], "clusters": []}


@router.websocket("/ws/{diagram_id}")
async def websocket_sync(websocket: WebSocket, diagram_id: str):
    await websocket.accept()

    # Send session.init
    diagram = diagram_service.get(diagram_id)
    init_payload: dict[str, Any] = {
        "diagram_id": diagram_id,
        "source_code": diagram.source_code if diagram else "",
        "layout_metadata": diagram.layout_metadata.model_dump() if diagram and diagram.layout_metadata else None,
        "graph_model": {"nodes": [], "edges": [], "clusters": []},
        "rendered_svg": "",
    }
    await websocket.send_json({"type": "session.init", "payload": init_payload})

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "payload": {"code": "INVALID_JSON", "message": "Invalid JSON", "recoverable": True},
                })
                continue

            msg_type = msg.get("type", "")
            msg_id = msg.get("id")
            payload = msg.get("payload", {})

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "code.update":
                source_code = payload.get("source_code", "")
                validation = validate_code(source_code)

                if not validation.valid:
                    await websocket.send_json({
                        "type": "validation.error",
                        "id": msg_id,
                        "payload": {
                            "errors": [
                                {"line": e.line, "column": e.column, "message": e.message, "severity": e.severity}
                                for e in validation.errors
                            ]
                        },
                    })
                else:
                    # Execute and render
                    exec_result = execute_diagram_code(source_code)
                    graph_model = _build_graph_model_from_exec(exec_result)

                    # Update diagram in storage
                    if diagram_id:
                        diagram_service.update(
                            diagram_id,
                            UpdateDiagramRequest(source_code=source_code),
                        )

                    await websocket.send_json({
                        "type": "render.result",
                        "id": msg_id,
                        "payload": {
                            "graph_model": graph_model,
                            "dot_source": exec_result.dot_source if exec_result.success else "",
                            "render_time_ms": 0,
                        },
                    })

            elif msg_type == "canvas.update":
                action = payload.get("action", "")
                # Canvas actions are mapped to code mutations server-side
                # For move_node, update layout sidecar only (no code change)
                if action == "move_node":
                    node_id = payload.get("node_id", "")
                    pos = payload.get("position", {})
                    d = diagram_service.get(diagram_id)
                    if d:
                        layout = d.layout_metadata or LayoutMetadata()
                        layout.node_positions[node_id] = {
                            "x": pos.get("x", 0),
                            "y": pos.get("y", 0),
                            "pinned": True,
                        }
                        diagram_service.update(
                            diagram_id, UpdateDiagramRequest(layout_metadata=layout)
                        )
                    # move_node doesn't change code — no code.sync needed
                else:
                    # For other actions (rename, add/remove edge/node), generate updated code
                    # Full implementation in T052-T053 (Phase 5)
                    d = diagram_service.get(diagram_id)
                    await websocket.send_json({
                        "type": "code.sync",
                        "id": msg_id,
                        "payload": {
                            "source_code": d.source_code if d else "",
                            "change_description": f"Canvas action: {action}",
                            "affected_lines": [],
                        },
                    })

            elif msg_type == "autosave.request":
                source_code = payload.get("source_code", "")
                layout_data = payload.get("layout_metadata")
                layout = LayoutMetadata(**layout_data) if layout_data else None

                diagram_service.update(
                    diagram_id,
                    UpdateDiagramRequest(source_code=source_code, layout_metadata=layout),
                )

                d = diagram_service.get(diagram_id)
                await websocket.send_json({
                    "type": "autosave.ack",
                    "id": msg_id,
                    "payload": {
                        "version": d.version if d else 0,
                        "saved_at": datetime.utcnow().isoformat() + "Z",
                    },
                })

            else:
                await websocket.send_json({
                    "type": "error",
                    "id": msg_id,
                    "payload": {
                        "code": "UNKNOWN_TYPE",
                        "message": f"Unknown message type: {msg_type}",
                        "recoverable": True,
                    },
                })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for diagram %s", diagram_id)
