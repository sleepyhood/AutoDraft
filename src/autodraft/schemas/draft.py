from __future__ import annotations

from pydantic import BaseModel, Field


class RunSelectedRequest(BaseModel):
    topic_ids: list[str] = Field(..., min_length=1)


class DraftResult(BaseModel):
    topic_id: str
    draft_id: str
    status: str  # EXPORTED | NEEDS_REVIEW | FAILED
    risk_score: int = Field(..., ge=0, le=100)
    summary: str
    export_html_ref: str


class RunSelectedResponse(BaseModel):
    drafts: list[DraftResult]
