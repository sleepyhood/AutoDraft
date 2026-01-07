from __future__ import annotations

from sqlalchemy.orm import Session

from autodraft.db.models import Topic


class TopicRepo:
    @staticmethod
    def create(db: Session, topic: Topic) -> Topic:
        db.add(topic)
        db.commit()
        db.refresh(topic)
        return topic

    @staticmethod
    def get(db: Session, topic_id: str) -> Topic | None:
        return db.get(Topic, topic_id)

    @staticmethod
    def update_status(db: Session, topic_id: str, status: str) -> None:
        t = db.get(Topic, topic_id)
        if not t:
            return
        t.status = status
        db.commit()
