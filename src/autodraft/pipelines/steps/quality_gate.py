from __future__ import annotations

import re
from datetime import datetime

from sqlalchemy.orm import Session

from autodraft.db.models import Draft
from autodraft.db.repos import DraftRepo

# 데모용 룰 (필요하면 계속 추가)
FORBIDDEN_PATTERNS: list[tuple[re.Pattern, int]] = [
    (re.compile(r"\b100%\b|무조건|확실"), 25),            # 과장
    (re.compile(r"합격\s*보장|단기간에"), 20),             # 과장/오해 소지
    (re.compile(r"010-\d{4}-\d{4}|전화번호|주민등록"), 40),  # 개인정보
]


def calc_risk_score(text: str) -> int:
    score = 0
    for pattern, weight in FORBIDDEN_PATTERNS:
        if pattern.search(text):
            score += weight
    # 너무 짧으면 품질/문맥 불확실 → 약간 가산
    if len(text) < 600:
        score += 10
    return min(100, score)


def apply_quality_gate(db: Session, draft: Draft, review_threshold: int = 30) -> Draft:
    """
    risk_score 계산 후 status 결정.
    - risk < threshold: EXPORTED(다음 단계에서 export 수행)
    - risk >= threshold: NEEDS_REVIEW(그래도 export는 만들어두는게 협업에 유리)
    """
    risk = calc_risk_score(draft.content_md)
    draft.risk_score = risk
    draft.status = "NEEDS_REVIEW" if risk >= review_threshold else "EXPORTED"
    draft.updated_at = datetime.utcnow()
    return DraftRepo.save(db, draft)
