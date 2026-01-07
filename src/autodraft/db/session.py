from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from autodraft.settings import settings

# SQLite를 쓸 때 멀티스레드 이슈 방지 옵션 필요
connect_args = {}
if settings.db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.db_url, echo=False, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    """
    FastAPI Depends에서 사용할 세션 공급자.
    (엔드포인트는 다음 단계에서)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
