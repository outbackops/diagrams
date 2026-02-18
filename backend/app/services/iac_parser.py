"""IaC parser service — send IaC content to GPT-4.1 with structured output schema.

Includes canonical layout enforcement (T096).
Stub — full implementation in Phase 6 (T057-T058).
"""

from __future__ import annotations

from app.services.ai_agent import CANONICAL_LAYOUT_RULES

# T096: The IaC parser prompt includes canonical layout rules
IAC_PARSER_SYSTEM_PROMPT = f"""You are an infrastructure-as-code analyzer. Given IaC files
(Terraform, CloudFormation, Bicep, or Kubernetes YAML), extract all cloud resources,
their relationships, and logical groupings.

{CANONICAL_LAYOUT_RULES}

When generating diagram code from IaC, apply these layout rules to produce
well-structured, readable architecture diagrams.
"""
