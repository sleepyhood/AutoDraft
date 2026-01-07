from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class TopicCandidate:
    title: str
    angle: str
    score: int


@dataclass
class DraftCandidate:
    content_md: str
    summary: str


class LLMClient:
    """
    지금은 stub.
    나중에 OpenAI/Claude 등으로 교체해도
    호출부(pipelines/steps)가 흔들리지 않게 인터페이스를 고정한다.
    """

    def generate_topics(self, pillar: str, audience: str, n: int) -> list[TopicCandidate]:
        templates = [
            ("{pillar} 관련 자주 묻는 질문 5가지", "FAQ형 구성(질문→답→정리)"),
            ("{audience}가 {pillar}에서 흔히 하는 실수 3가지", "실수→원인→해결 루틴→연습"),
            ("{pillar}를 10분 만에 이해시키는 설명법", "비유+예시+체크리스트"),
            ("이번 주 {pillar} 핵심 요약 + 숙제 가이드", "요약→예시→숙제포인트"),
        ]
        out: list[TopicCandidate] = []
        for i in range(n):
            title_tpl, angle = templates[i % len(templates)]
            title = title_tpl.format(pillar=pillar, audience=audience)
            score = max(40, min(95, 85 - i))
            out.append(TopicCandidate(title=title, angle=angle, score=score))
        return out

    def generate_draft(self, title: str, angle: str, pillar: str, audience: str) -> DraftCandidate:
        summary = f"{title}에 대해 {angle} 흐름으로 정리합니다. 대상: {audience}"
        content_md = f"""# {title}

> 대상: {audience}  
> 카테고리: {pillar}  
> 구성: {angle}

## 1) 문제 상황
- 왜 어려운지 2~3가지 포인트로 정리합니다.

## 2) 핵심 개념
- 쉬운 말로 정의
- 예시 1개

## 3) 적용 루틴
1. 오늘 할 일
2. 내일 할 일
3. 체크리스트

## 4) 연습/숙제
- 연습문제 2개(또는 체크 질문 3개)

## 마무리
- 다음 글 예고 / 과장 없는 CTA
"""
        return DraftCandidate(content_md=content_md, summary=summary)
