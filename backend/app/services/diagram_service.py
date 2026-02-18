"""Diagram CRUD service — create, read, update, delete, versioning.

Uses in-memory storage for MVP. Production would use a database.
"""

from __future__ import annotations

from datetime import datetime

from app.models.diagram import (
    CreateDiagramRequest,
    Diagram,
    DiagramStatus,
    DiagramVersion,
    UpdateDiagramRequest,
)


class DiagramService:
    """In-memory diagram storage and CRUD operations."""

    def __init__(self) -> None:
        self._diagrams: dict[str, Diagram] = {}
        self._versions: dict[str, list[DiagramVersion]] = {}

    def create(self, request: CreateDiagramRequest) -> Diagram:
        diagram = Diagram(
            name=request.name,
            theme=request.theme,
            direction=request.direction,
            status=DiagramStatus.DRAFT,
        )
        self._diagrams[diagram.id] = diagram
        self._versions[diagram.id] = []
        return diagram

    def get(self, diagram_id: str) -> Diagram | None:
        return self._diagrams.get(diagram_id)

    def list_all(self) -> list[Diagram]:
        return list(self._diagrams.values())

    def update(self, diagram_id: str, request: UpdateDiagramRequest) -> Diagram | None:
        diagram = self._diagrams.get(diagram_id)
        if diagram is None:
            return None

        # Snapshot current version before updating
        if request.source_code is not None and request.source_code != diagram.source_code:
            self._snapshot_version(diagram, "Code updated")

        if request.name is not None:
            diagram.name = request.name
        if request.source_code is not None:
            diagram.source_code = request.source_code
            diagram.status = DiagramStatus.EDITING
        if request.layout_metadata is not None:
            diagram.layout_metadata = request.layout_metadata

        diagram.updated_at = datetime.utcnow()
        diagram.version += 1
        return diagram

    def update_from_generation(
        self,
        diagram_id: str,
        source_code: str,
        dot_source: str | None = None,
        providers: list[str] | None = None,
    ) -> Diagram | None:
        diagram = self._diagrams.get(diagram_id)
        if diagram is None:
            return None

        self._snapshot_version(diagram, "AI generated")
        diagram.source_code = source_code
        diagram.dot_source = dot_source
        diagram.providers = providers or []
        diagram.status = DiagramStatus.GENERATED
        diagram.updated_at = datetime.utcnow()
        diagram.version += 1
        return diagram

    def delete(self, diagram_id: str) -> bool:
        if diagram_id in self._diagrams:
            del self._diagrams[diagram_id]
            self._versions.pop(diagram_id, None)
            return True
        return False

    def get_versions(self, diagram_id: str) -> list[DiagramVersion]:
        return self._versions.get(diagram_id, [])

    def _snapshot_version(self, diagram: Diagram, change_summary: str) -> None:
        version = DiagramVersion(
            diagram_id=diagram.id,
            version=diagram.version,
            source_code=diagram.source_code,
            layout_metadata=diagram.layout_metadata,
            change_summary=change_summary,
        )
        if diagram.id not in self._versions:
            self._versions[diagram.id] = []
        self._versions[diagram.id].append(version)


# Singleton instance
diagram_service = DiagramService()
