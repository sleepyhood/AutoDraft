from __future__ import annotations
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
    )

    db_url: str = "sqlite:///./autodraft.db"

    llm_provider: str = "stub"     # env: LLM_PROVIDER
    llm_model: str = "gpt-5-mini"  # env: LLM_MODEL

    export_dir: str = str(BASE_DIR / "exports")

    demo_api_token: str = "change-me"

    openai_api_key: str | None = None  # env: OPENAI_API_KEY

settings = Settings()
