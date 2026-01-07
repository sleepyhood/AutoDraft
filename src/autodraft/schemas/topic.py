from __future__ import annotations

from pydantic import BaseModel, Field


class GenerateTopicsRequest(BaseModel):
    pillar: str = Field(..., description="예: 📢 공지, 🧠 학습법 등")
    audience: str = Field(..., description="예: 👶 학생-초급, 👨‍👩‍👧 학부모 등")
    n: int = Field(10, ge=1, le=50)


class TopicIdea(BaseModel):
    topic_id: str
    title: str = Field(..., max_length=200)
    angle: str = Field(..., max_length=300)
    score: int = Field(..., ge=0, le=100)


class GenerateTopicsResponse(BaseModel):
    items: list[TopicIdea]
