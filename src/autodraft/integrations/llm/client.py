from __future__ import annotations

import json
import re
from dataclasses import dataclass

from autodraft.settings import settings
from pydantic import BaseModel, Field

@dataclass
class TopicCandidate:
    title: str
    angle: str
    score: int

@dataclass
class DraftCandidate:
    content_md: str
    summary: str


from pydantic import BaseModel, Field

class TopicItemOut(BaseModel):
    title: str
    angle: str
    score: int = Field(ge=0, le=100)

class TopicListOut(BaseModel):
    items: list[TopicItemOut]

class DraftOut(BaseModel):
    summary: str
    content_md: str

def _openai_parse(self, prompt: str, out_model):
    return self._openai.responses.parse(
        model=self.model,
        input=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        text_format=out_model,
    ).output_parsed


def _extract_json(text: str) -> str | None:
    # 모델이 설명을 섞어도 JSON 덩어리만 뽑아내기(가장 큰 {} 또는 [])
    m1 = re.search(r"(\{.*\})", text, flags=re.DOTALL)
    m2 = re.search(r"(\[.*\])", text, flags=re.DOTALL)
    # 더 긴 쪽 선택
    cand = []
    if m1: cand.append(m1.group(1))
    if m2: cand.append(m2.group(1))
    if not cand: return None
    return max(cand, key=len)

class LLMClient:
    def __init__(self):
        self.provider = (settings.llm_provider or "stub").lower()
        self.model = settings.llm_model

        self._openai = None
        if self.provider == "openai":
            from openai import OpenAI
            # OpenAI()는 OPENAI_API_KEY 환경변수를 사용(또는 api_key 인자로 직접 전달)
            if settings.openai_api_key:
                self._openai = OpenAI(api_key=settings.openai_api_key)
            else:
                self._openai = OpenAI()

    # ---------- stub ----------
    def _stub_topics(self, pillar: str, audience: str, n: int) -> list[TopicCandidate]:
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

    def _stub_draft(self, title: str, angle: str, pillar: str, audience: str) -> DraftCandidate:
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

    # ---------- openai ----------
    def _openai_output_text(self, prompt: str) -> str:
        # Responses API 사용 (OpenAI 권장 인터페이스) :contentReference[oaicite:2]{index=2}
        r = self._openai.responses.create(model=self.model, input=prompt)
        return r.output_text

    def generate_topics(self, pillar: str, audience: str, n: int) -> list[TopicCandidate]:
        if self.provider != "openai" or not self._openai:
            return self._stub_topics(pillar, audience, n)

        prompt = f"""
너는 한국어 블로그 글 기획자다.
주제 영역(pillar)과 대상(audience)을 보고, 블로그 글 제목 후보 {n}개를 만들어라.

반드시 JSON 배열만 출력:
[
  {{"title":"...","angle":"...","score":0-100}},
  ...
]

조건:
- title은 40자 이내
- angle은 한 문장(구성/전개 요약)
- score는 실전 유용도 점수(0~100)
pillar={pillar}
audience={audience}
"""
        text = self._openai_output_text(prompt)
        j = _extract_json(text)
        if not j:
            return self._stub_topics(pillar, audience, n)

        try:
            arr = json.loads(j)
            out = []
            for x in arr[:n]:
                out.append(TopicCandidate(
                    title=str(x["title"]),
                    angle=str(x["angle"]),
                    score=int(x.get("score", 70)),
                ))
            return out
        except Exception:
            return self._stub_topics(pillar, audience, n)

    def generate_draft(self, title: str, angle: str, pillar: str, audience: str) -> DraftCandidate:
        if self.provider != "openai" or not self._openai:
            return self._stub_draft(title, angle, pillar, audience)

        prompt = f"""
너는 한국어 블로그 글 작성자다.
아래 정보를 바탕으로 '네이버 블로그에 붙여넣기 쉬운' 마크다운 초안을 작성해라.

반드시 JSON 객체만 출력:
{{
  "summary": "한 문장 요약",
  "content_md": "마크다운 전체"
}}

작성 규칙:
- 과장/보장 표현(100%, 무조건, 합격보장 등) 금지
- H1 1개, H2 3~6개
- 목록(ul/ol), 인용문(> ) 포함
- 마지막에 짧은 CTA(상담 유도는 과장 없이)
title={title}
angle={angle}
pillar={pillar}
audience={audience}
"""
        text = self._openai_output_text(prompt)
        j = _extract_json(text)
        if not j:
            return self._stub_draft(title, angle, pillar, audience)

        try:
            obj = json.loads(j)
            return DraftCandidate(
                summary=str(obj["summary"]),
                content_md=str(obj["content_md"]),
            )
        except Exception:
            return self._stub_draft(title, angle, pillar, audience)
