from __future__ import annotations

from sqlalchemy.orm import Session

from autodraft.db.models import Draft


class DraftRepo:
    @staticmethod
    def create(db: Session, draft: Draft) -> Draft:
        db.add(draft)
        db.commit()
        db.refresh(draft)
        return draft

    @staticmethod
    def get(db: Session, draft_id: str) -> Draft | None:
        return db.get(Draft, draft_id)

    @staticmethod
    def save(db: Session, draft: Draft) -> Draft:
        """
        draft 객체에 필드 변경 후 호출하면 commit/refresh.
        """
        db.add(draft)
        db.commit()
        db.refresh(draft)
        return draft
