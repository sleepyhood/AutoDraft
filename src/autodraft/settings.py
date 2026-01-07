from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # DB
    db_url: str = "sqlite:///./autodraft.db"

    # LLM (지금은 스텁이지만, 나중에 교체 대비)
    llm_provider: str = "stub"   # stub | openai | anthropic ...
    llm_api_key: str | None = None
    llm_model: str = "gpt-4.1-mini"

    # Export (다음 단계에서 사용)
    export_dir: str = "./exports"

    # 기타
    demo_api_token: str = "change-me"

settings = Settings()

