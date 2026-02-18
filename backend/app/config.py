"""Settings and environment configuration using Pydantic BaseSettings."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_deployment_fallback: str = "gpt-4o"
    azure_openai_api_version: str = "2024-12-01-preview"

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
