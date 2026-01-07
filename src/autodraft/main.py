from __future__ import annotations

import hashlib
import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from autodraft.db.base import Base
from autodraft.db.session import engine, get_db
from autodraft.integrations.llm import LLMClient
from autodraft.pipelines.orchestrator import run_selected
from autodraft.pipelines.steps.topic_factory import generate_topics
from autodraft.schemas.draft import RunSelectedRequest, RunSelectedResponse
from autodraft.schemas.topic import GenerateTopicsRequest, GenerateTopicsResponse
from autodraft.settings import settings


api_key_header = APIKeyHeader(name="X-DEMO-TOKEN", auto_error=False)


def verify_demo_token(api_key: str | None = Depends(api_key_header)) -> None:
    configured = (settings.demo_api_token or "").strip()
    received = (api_key or "").strip()

    if not configured or configured == "change-me":
        raise HTTPException(status_code=500, detail="DEMO_API_TOKEN not set")
    if received != configured:
        raise HTTPException(status_code=401, detail="Invalid X-DEMO-TOKEN")


def create_app() -> FastAPI:
    app = FastAPI(title="AutoDraft Demo", version="0.3.0")

    # exports 디렉토리 보장 + 정적 서빙
    export_dir = Path(settings.export_dir).resolve()
    export_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/exports", StaticFiles(directory=str(export_dir)), name="exports")

    llm = LLMClient()

    @app.on_event("startup")
    def _startup() -> None:
        Base.metadata.create_all(bind=engine)

    @app.get("/health")
    def health():
        return {
            "ok": True,
            "demo_token_configured": settings.demo_api_token != "change-me",
            "llm_provider": settings.llm_provider,
            "llm_model": settings.llm_model,
        }

    # ---- debug ----
    @app.get("/debug/auth", dependencies=[Depends(verify_demo_token)])
    def debug_auth():
        return {"ok": True}

    @app.get("/debug/token_fingerprint")
    def token_fingerprint():
        configured = (settings.demo_api_token or "").strip().encode("utf-8")
        fp = hashlib.sha256(configured).hexdigest()[:12]
        return {"configured_fp": fp, "configured_len": len(configured)}

    @app.get("/debug/env_info")
    def env_info():
        cwd = str(Path.cwd())
        env_path = str(Path(".env").resolve())
        env_exists = Path(".env").exists()

        configured = (settings.demo_api_token or "").strip()
        env_token = (os.environ.get("DEMO_API_TOKEN") or "").strip()

        def fp(s: str) -> str:
            return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12] if s else ""

        return {
            "cwd": cwd,
            "env_path": env_path,
            "env_exists": env_exists,
            "configured_len": len(configured),
            "configured_fp": fp(configured),
            "os_env_present": bool(env_token),
            "os_env_len": len(env_token),
            "os_env_fp": fp(env_token),
        }

    @app.get("/debug/exports")
    def debug_exports():
        p = Path(settings.export_dir).resolve()
        files = [x.name for x in p.glob("*.html")][:20] if p.exists() else []
        return {
            "export_dir": str(p),
            "exists": p.exists(),
            "html_count": len(list(p.glob("*.html"))) if p.exists() else 0,
            "sample": files,
        }

    # ---- api ----
    @app.post(
        "/topics/generate",
        response_model=GenerateTopicsResponse,
        dependencies=[Depends(verify_demo_token)],
    )
    def api_generate_topics(req: GenerateTopicsRequest, db: Session = Depends(get_db)) -> GenerateTopicsResponse:
        items = generate_topics(db=db, llm=llm, pillar=req.pillar, audience=req.audience, n=req.n)
        return GenerateTopicsResponse(items=items)

    @app.post(
        "/pipeline/run_selected",
        response_model=RunSelectedResponse,
        dependencies=[Depends(verify_demo_token)],
    )
    def api_run_selected(req: RunSelectedRequest, db: Session = Depends(get_db)) -> RunSelectedResponse:
        drafts = run_selected(db=db, llm=llm, topic_ids=req.topic_ids)
        return RunSelectedResponse(drafts=drafts)

    return app


app = create_app()
