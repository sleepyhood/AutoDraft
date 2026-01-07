from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException
from sqlalchemy.orm import Session

from autodraft.db.base import Base
from autodraft.db.session import engine, get_db
from autodraft.integrations.llm import LLMClient
from autodraft.pipelines.steps.topic_factory import generate_topics
from autodraft.pipelines.orchestrator import run_selected
from autodraft.schemas.topic import GenerateTopicsRequest, GenerateTopicsResponse
from autodraft.schemas.draft import RunSelectedRequest, RunSelectedResponse
from autodraft.settings import settings


def verify_demo_token(x_demo_token: str | None = Header(default=None)) -> None:
    if not settings.demo_api_token or settings.demo_api_token == "change-me":
        raise HTTPException(
            status_code=500,
            detail="demo_api_token is not set. Please set DEMO_API_TOKEN in env/.env",
        )
    if x_demo_token != settings.demo_api_token:
        raise HTTPException(status_code=401, detail="Invalid X-DEMO-TOKEN")


def create_app() -> FastAPI:
    app = FastAPI(title="AutoDraft Demo", version="0.3.0")

    llm = LLMClient()  # 현재 stub, 나중에 provider별로 교체

    @app.on_event("startup")
    def _startup() -> None:
        Base.metadata.create_all(bind=engine)

    @app.get("/health")
    def health():
        return {"ok": True}

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
