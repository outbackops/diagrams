"""Azure AI Foundry agent definition — defines the diagram agent with
generate/refine/import tools using the Microsoft Agent Framework (T074, T076).
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class DiagramAgent:
    """Diagram Agent for Azure AI Foundry.

    Wraps the backend services (ai_agent, iac_parser, export_service) as
    callable agent tools. Deployed as a Hosted Agent via the hosting adapter.
    """

    def __init__(self) -> None:
        self.name = "diagram-agent"
        self.description = (
            "AI-powered architecture diagramming agent. Generates, refines, "
            "and exports cloud architecture diagrams using diagram-as-code."
        )
        self.tools = self._register_tools()

    def _register_tools(self) -> list[dict[str, Any]]:
        """Register agent tools for Foundry."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "generate_diagram",
                    "description": "Generate an architecture diagram from a natural-language description",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "Natural language architecture description",
                            },
                            "providers": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional cloud providers to use",
                            },
                        },
                        "required": ["prompt"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "refine_diagram",
                    "description": "Modify an existing diagram based on a follow-up instruction",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "diagram_id": {
                                "type": "string",
                                "description": "ID of the diagram to modify",
                            },
                            "prompt": {
                                "type": "string",
                                "description": "Modification instruction",
                            },
                        },
                        "required": ["diagram_id", "prompt"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "import_iac",
                    "description": "Generate a diagram from infrastructure-as-code content",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "IaC file content",
                            },
                            "format": {
                                "type": "string",
                                "enum": ["terraform", "cloudformation", "bicep", "kubernetes"],
                            },
                        },
                        "required": ["content", "format"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "export_diagram",
                    "description": "Export a diagram as an image or code file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "diagram_id": {
                                "type": "string",
                                "description": "ID of the diagram",
                            },
                            "format": {
                                "type": "string",
                                "enum": ["png", "svg", "pdf", "py"],
                            },
                        },
                        "required": ["diagram_id", "format"],
                    },
                },
            },
        ]
