from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from autodraft.db.models import Draft, Topic
from autodraft.db.repos import DraftRepo
from autodraft.integrations.llm import LLMClient


def generate_draft(db: Session, llm: LLMClient, topic: Topic) -> Draft:
    """
    topic 기반으로 초안 생성(Draft row 생성).
    """
    draft_id = f"d_{uuid.uuid4().hex[:10]}"
    out = llm.generate_draft(
        title=topic.title,
        angle=topic.angle,
        pillar=topic.pillar,
        audience=topic.audience,
    )

    now = datetime.utcnow()
    draft = Draft(
        id=draft_id,
        topic_id=topic.id,
        title=topic.title,
        content_md=out.content_md,
        summary=out.summary,
        risk_score=0,
        status="DRAFTED",
        export_html_ref="",
        last_error=None,
        updated_at=now,
    )
    return DraftRepo.create(db, draft)
