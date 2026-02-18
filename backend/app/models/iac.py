"""IaCSource and ParsedResource Pydantic models per data-model.md."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IaCFormat(str, Enum):
    TERRAFORM = "terraform"
    CLOUDFORMATION = "cloudformation"
    BICEP = "bicep"
    KUBERNETES = "kubernetes"


class SourceType(str, Enum):
    FILE_UPLOAD = "file_upload"
    REPOSITORY = "repository"


class ParsedResource(BaseModel):
    resource_type: str
    resource_name: str
    mapped_node: str | None = None
    relationships: list[str] = Field(default_factory=list)


class IaCSource(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    diagram_id: str | None = None
    source_type: SourceType = SourceType.FILE_UPLOAD
    iac_format: IaCFormat = IaCFormat.TERRAFORM
    file_name: str | None = None
    repo_url: str | None = None
    content: str = ""
    parsed_resources: list[ParsedResource] | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ImportResponse(BaseModel):
    diagram: dict[str, Any]
    parsed_resources: list[ParsedResource] = Field(default_factory=list)
    unsupported_services: list[str] = Field(default_factory=list)
    explanation: str = ""


class ImportRepoRequest(BaseModel):
    repo_url: str
    branch: str = "main"
    path_filter: str | None = None


class ConfirmRepoImportRequest(BaseModel):
    repo_url: str
    selected_files: list[str]


class RepoScanResponse(BaseModel):
    files: list[dict[str, Any]] = Field(default_factory=list)
    total_resources: int = 0
