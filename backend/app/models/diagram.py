"""Diagram and DiagramVersion Pydantic models per data-model.md."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DiagramStatus(str, Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    EDITING = "editing"


class DiagramTheme(str, Enum):
    NEUTRAL = "neutral"
    PASTEL = "pastel"
    BLUES = "blues"
    GREENS = "greens"
    ORANGE = "orange"


class DiagramDirection(str, Enum):
    TB = "TB"
    BT = "BT"
    LR = "LR"
    RL = "RL"


class LayoutMetadata(BaseModel):
    version: int = 1
    engine: str = "dot"
    node_positions: dict[str, dict[str, Any]] = Field(default_factory=dict)
    cluster_bounds: dict[str, dict[str, Any]] = Field(default_factory=dict)
    viewport: dict[str, float] = Field(
        default_factory=lambda: {"zoom": 1.0, "pan_x": 0.0, "pan_y": 0.0}
    )


class Diagram(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    name: str
    source_code: str = ""
    dot_source: str | None = None
    layout_metadata: LayoutMetadata | None = None
    providers: list[str] = Field(default_factory=list)
    theme: DiagramTheme = DiagramTheme.NEUTRAL
    direction: DiagramDirection = DiagramDirection.LR
    status: DiagramStatus = DiagramStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1


class DiagramVersion(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    diagram_id: str
    version: int
    source_code: str
    layout_metadata: LayoutMetadata | None = None
    change_summary: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CreateDiagramRequest(BaseModel):
    name: str = Field(max_length=200)
    theme: DiagramTheme = DiagramTheme.NEUTRAL
    direction: DiagramDirection = DiagramDirection.LR


class UpdateDiagramRequest(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    source_code: str | None = None
    layout_metadata: LayoutMetadata | None = None
