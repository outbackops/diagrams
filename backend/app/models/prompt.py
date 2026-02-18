"""Prompt and AIDecisionLog Pydantic models per data-model.md."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PromptType(str, Enum):
    GENERATE = "generate"
    REFINE = "refine"
    IMPORT = "import"


class Prompt(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    diagram_id: str | None = None
    user_text: str = Field(max_length=5000)
    prompt_type: PromptType = PromptType.GENERATE
    ai_model: str = ""
    ai_response_code: str | None = None
    ai_explanation: str | None = None
    ai_assumptions: list[str] | None = None
    prompt_hash: str = ""
    duration_ms: int | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def compute_hash(self, model: str, parameters: dict[str, Any] | None = None) -> str:
        """Compute SHA-256 hash of user_text + model + parameters for reproducibility."""
        payload = f"{self.user_text}|{model}|{parameters or {}}"
        self.prompt_hash = hashlib.sha256(payload.encode()).hexdigest()
        return self.prompt_hash


class GeneratePromptRequest(BaseModel):
    prompt: str = Field(max_length=5000)
    providers: list[str] | None = None
    theme: str = "neutral"
    direction: str = "LR"


class RefinePromptRequest(BaseModel):
    diagram_id: str
    prompt: str = Field(max_length=5000)


class PromptResponse(BaseModel):
    diagram: dict[str, Any]
    explanation: str = ""
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    diff: str | None = None
    model_used: str = ""
    prompt_hash: str = ""
