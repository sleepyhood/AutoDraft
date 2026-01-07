from __future__ import annotations

from sqlalchemy.orm import Session

from autodraft.db.repos import TopicRepo
from autodraft.integrations.llm import LLMClient
from autodraft.schemas.draft import DraftResult

from autodraft.pipelines.steps.draft import generate_draft
from autodraft.pipelines.steps.quality_gate import apply_quality_gate
from autodraft.pipelines.steps.export import export_draft_html


def run_selected(db: Session, llm: LLMClient, topic_ids: list[str]) -> list[DraftResult]:
    """
    선택된 topic_ids에 대해:
    - Draft 생성
    - Quality Gate(risk_score, status)
    - Export HTML 생성
    반환: DraftResult 리스트(시트에 적기 좋음)
    """
    results: list[DraftResult] = []

    for topic_id in topic_ids:
        try:
            topic = TopicRepo.get(db, topic_id)
            if not topic:
                raise ValueError(f"Topic not found: {topic_id}")

            draft = generate_draft(db, llm, topic)
            draft = apply_quality_gate(db, draft, review_threshold=30)
            draft = export_draft_html(db, draft)

            # topic 처리 완료 표시(리스크 높아도 “초안 생성 완료”는 DONE)
            TopicRepo.update_status(db, topic_id, "DONE")

            results.append(
                DraftResult(
                    topic_id=topic_id,
                    draft_id=draft.id,
                    status=draft.status,         # EXPORTED 또는 NEEDS_REVIEW
                    risk_score=draft.risk_score,
                    summary=draft.summary,
                    export_html_ref=draft.export_html_ref,
                )
            )

        except Exception:
            TopicRepo.update_status(db, topic_id, "ERROR")
            results.append(
                DraftResult(
                    topic_id=topic_id,
                    draft_id="",
                    status="FAILED",
                    risk_score=100,
                    summary="",
                    export_html_ref="",
                )
            )

    return results
