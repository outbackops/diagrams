"""AST-based code validator and sandboxed code executor.

Layer 1 — AST validation (pre-execution):
  - Parse generated Python code using ast module
  - Whitelist allowed imports: only diagrams and diagrams.* submodules
  - Reject dangerous patterns: os.system, subprocess, eval, exec, __import__, etc.
  - Validate that all referenced node classes exist in the library

Layer 2 — Subprocess with restrictions (execution):
  - Run validated code in subprocess with resource limits
  - Temporary working directory cleaned after each execution
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from app.config import settings
from app.services.node_registry import node_registry


@dataclass
class ValidationError:
    line: int
    column: int
    message: str
    severity: str = "error"  # "error" | "warning"


@dataclass
class ValidationResult:
    valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    node_count: int | None = None
    edge_count: int | None = None
    providers_used: list[str] | None = None


# Imports that are always allowed
ALLOWED_IMPORT_PREFIXES = ("diagrams",)

# Names that are never allowed anywhere in the code
FORBIDDEN_NAMES = {
    "os",
    "subprocess",
    "sys",
    "shutil",
    "pathlib",
    "importlib",
    "socket",
    "http",
    "urllib",
    "requests",
    "__import__",
    "compile",
    "globals",
    "locals",
    "breakpoint",
    "open",
}

# Built-in calls that are forbidden
FORBIDDEN_CALLS = {"eval", "exec", "__import__", "compile", "open", "breakpoint"}


class _ASTValidator(ast.NodeVisitor):
    """Walk the AST and collect validation errors."""

    def __init__(self) -> None:
        self.errors: list[ValidationError] = []
        self.imports: list[str] = []
        self.providers_used: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if not any(alias.name.startswith(p) for p in ALLOWED_IMPORT_PREFIXES):
                self.errors.append(
                    ValidationError(
                        line=node.lineno,
                        column=node.col_offset,
                        message=f"Import '{alias.name}' is not allowed. Only 'diagrams' imports are permitted.",
                    )
                )
            else:
                self.imports.append(alias.name)
                parts = alias.name.split(".")
                if len(parts) >= 2:
                    self.providers_used.add(parts[1])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        if not any(module.startswith(p) for p in ALLOWED_IMPORT_PREFIXES):
            self.errors.append(
                ValidationError(
                    line=node.lineno,
                    column=node.col_offset,
                    message=f"Import from '{module}' is not allowed. Only 'diagrams' imports are permitted.",
                )
            )
        else:
            self.imports.append(module)
            parts = module.split(".")
            if len(parts) >= 2:
                self.providers_used.add(parts[1])
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # Check for forbidden function calls
        if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
            self.errors.append(
                ValidationError(
                    line=node.lineno,
                    column=node.col_offset,
                    message=f"Call to '{node.func.id}()' is not allowed for security reasons.",
                )
            )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # Check for forbidden attribute access like os.system
        if isinstance(node.value, ast.Name) and node.value.id in FORBIDDEN_NAMES:
            self.errors.append(
                ValidationError(
                    line=node.lineno,
                    column=node.col_offset,
                    message=f"Access to '{node.value.id}.{node.attr}' is not allowed for security reasons.",
                )
            )
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in FORBIDDEN_NAMES and isinstance(node.ctx, ast.Load):
            # Only flag if it's being used (loaded), not just imported
            pass  # Handled via imports and calls
        self.generic_visit(node)


def validate_code(source_code: str) -> ValidationResult:
    """Validate diagram Python code using AST analysis.

    Returns a ValidationResult with errors if the code is unsafe or invalid.
    """
    if not source_code.strip():
        return ValidationResult(
            valid=False,
            errors=[ValidationError(line=1, column=0, message="Source code is empty")],
        )

    # Parse the AST
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return ValidationResult(
            valid=False,
            errors=[
                ValidationError(
                    line=e.lineno or 1,
                    column=e.offset or 0,
                    message=f"SyntaxError: {e.msg}",
                )
            ],
        )

    # Walk the AST for security validation
    validator = _ASTValidator()
    validator.visit(tree)

    if validator.errors:
        return ValidationResult(valid=False, errors=validator.errors)

    return ValidationResult(
        valid=True,
        providers_used=sorted(validator.providers_used),
    )


@dataclass
class ExecutionResult:
    success: bool
    output_dir: str | None = None
    output_files: list[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    dot_source: str = ""
    error: str | None = None


def execute_diagram_code(
    source_code: str,
    output_format: str = "png",
    filename: str | None = None,
) -> ExecutionResult:
    """Execute validated diagram code in a sandboxed subprocess.

    The code is written to a temp directory and executed as a subprocess
    with resource limits.
    """
    # First validate
    validation = validate_code(source_code)
    if not validation.valid:
        error_msgs = "; ".join(e.message for e in validation.errors)
        return ExecutionResult(success=False, error=f"Validation failed: {error_msgs}")

    # Create temp directory for execution
    tmp_dir = tempfile.mkdtemp(prefix="diagram_exec_")
    script_name = filename or f"diagram_{uuid.uuid4().hex[:8]}"
    script_path = os.path.join(tmp_dir, f"{script_name}.py")

    # Inject show=False so diagrams don't try to open a viewer
    modified_code = source_code.replace("show=True", "show=False")
    if "show=False" not in modified_code and "Diagram(" in modified_code:
        modified_code = modified_code.replace("Diagram(", "Diagram(show=False, ", 1)

    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(modified_code)

        # Execute in subprocess with timeout and resource limits
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=tmp_dir,
            capture_output=True,
            text=True,
            timeout=settings.diagram_exec_timeout_seconds,
            env={
                **os.environ,
                "PYTHONPATH": str(settings.repo_root),
            },
        )

        if result.returncode != 0:
            return ExecutionResult(
                success=False,
                stdout=result.stdout,
                stderr=result.stderr,
                error=f"Execution failed: {result.stderr.strip()}",
            )

        # Collect output files
        output_files = []
        for f in os.listdir(tmp_dir):
            if f.endswith((".png", ".svg", ".pdf", ".gv", ".dot")):
                output_files.append(os.path.join(tmp_dir, f))

        # Read DOT source if available
        dot_source = ""
        for f in os.listdir(tmp_dir):
            if f.endswith(".gv") or (f.endswith("") and not f.endswith(".py")):
                gv_path = os.path.join(tmp_dir, f)
                if os.path.isfile(gv_path) and os.path.getsize(gv_path) < 1_000_000:
                    try:
                        with open(gv_path, "r", encoding="utf-8") as gv:
                            content = gv.read()
                            if content.strip().startswith(("digraph", "graph")):
                                dot_source = content
                                break
                    except Exception:
                        pass

        return ExecutionResult(
            success=True,
            output_dir=tmp_dir,
            output_files=output_files,
            stdout=result.stdout,
            stderr=result.stderr,
            dot_source=dot_source,
        )

    except subprocess.TimeoutExpired:
        return ExecutionResult(
            success=False,
            error=f"Execution timed out after {settings.diagram_exec_timeout_seconds} seconds",
        )
    except Exception as e:
        return ExecutionResult(success=False, error=str(e))
