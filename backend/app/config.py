"""Settings and environment configuration using Pydantic BaseSettings."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Azure AI Foundry
    azure_ai_project_connection_string: str = ""
    azure_openai_deployment: str = "gpt-4.1"
    azure_openai_deployment_fallback: str = "gpt-4.1-mini"

    # Application
    app_env: str = "development"
    log_level: str = "info"
    cors_origins: list[str] = ["http://localhost:5173"]

    # Diagram execution
    diagram_exec_timeout_seconds: int = 30
    diagram_exec_max_memory_mb: int = 512
    diagram_storage_dir: str = "./data/diagrams"

    # Paths — resolved relative to repo root
    repo_root: Path = Path(__file__).resolve().parent.parent.parent
    diagrams_lib_dir: Path = repo_root / "diagrams"
    resources_dir: Path = repo_root / "resources"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
