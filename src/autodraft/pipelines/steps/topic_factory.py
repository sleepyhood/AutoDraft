from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from autodraft.db.models import Topic
from autodraft.db.repos import TopicRepo
from autodraft.integrations.llm import LLMClient
from autodraft.schemas.topic import TopicIdea


def generate_topics(db: Session, llm: LLMClient, pillar: str, audience: str, n: int) -> list[TopicIdea]:
    """
    LLM(현재 stub 포함)로 토픽 후보 생성 + DB 저장.
    반환은 시트에 꽂기 좋은 TopicIdea 리스트.
    """
    now = datetime.utcnow()
    candidates = llm.generate_topics(pillar=pillar, audience=audience, n=n)

    items: list[TopicIdea] = []
    for c in candidates:
        topic_id = f"t_{uuid.uuid4().hex[:10]}"
        topic = Topic(
            id=topic_id,
            pillar=pillar,
            audience=audience,
            title=c.title,
            angle=c.angle,
            score=int(c.score),
            status="NEW",
            created_at=now,
        )
        TopicRepo.create(db, topic)

        items.append(
            TopicIdea(
                topic_id=topic_id,
                title=topic.title,
                angle=topic.angle,
                score=topic.score,
            )
        )
    return items
