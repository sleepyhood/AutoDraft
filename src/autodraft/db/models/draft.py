from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from autodraft.db.base import Base


class Draft(Base):
    __tablename__ = "drafts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # e.g., d_xxxxx
    topic_id: Mapped[str] = mapped_column(String(64), ForeignKey("topics.id"), nullable=False)

    title: Mapped[str] = mapped_column(String(200), nullable=False)

    content_md: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFTED")

    export_html_ref: Mapped[str] = mapped_column(Text, nullable=False, default="")  # 다음 단계에서 채움
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
