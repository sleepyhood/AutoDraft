# AutoDraft Demo (Google Sheets + FastAPI + GPT)

구글 시트를 **협업/승인 보드(컨트롤 패널)** 로 사용하고, FastAPI 서버가 **Topic 생성 → Draft 생성 → QA(리스크 점수) → Export HTML**까지 처리하는 최소 데모.

> 목적: “LLM 심문”을 줄이고, **버튼 2번으로** 초안 생성 파이프라인이 돌아가게 만들기.

---

## 데모 성공 조건

* [ ] (시트 버튼 1) `Generate Topics` 실행 → `Topics` 탭에 **주제 후보 10개** 자동 삽입
* [ ] 운영자가 몇 개를 `SELECTED`로 변경
* [ ] (시트 버튼 1) `Run Selected` 실행 → `Drafts` 탭에 **Draft/QA/Export 결과**가 자동 삽입
* [ ] 운영자는 `export_html_ref`(링크/경로)로 결과물을 열어 **네이버에 복붙**만 한다

### 이번 데모에서 제외(의도적으로 미룸)

* Playwright 기반 웹 크롤링(리서치) → 스텁/고정 텍스트 또는 링크만
* Minio/S3 스토리지 → 로컬 파일 저장
* 완전 자동 업로드(네이버 발행) → 범위 밖(사람이 최종 발행)

---

## 아키텍처(개요)

* **Google Sheets**: 협업 UI / 상태 관리(NEW, SELECTED, DONE)
* **Apps Script**: 시트 메뉴 버튼 → FastAPI 호출
* **FastAPI**: LLM 호출 + 스키마 검증 + Draft/QA/Export 생성
* **DB(SQLite)**: Topic/Draft 저장(재현성/로그 목적)
* **Export**: HTML 파일로 저장 후 참조(ref)만 시트에 기록

---

## 요구 사항

* Python 3.11+
* (권장) uv/poetry 중 택1
* Google Sheets + Apps Script 권한

---

## 파일 구조(대략)

```text
autodraft-demo/
├─ README.md
├─ pyproject.toml
├─ .env.example
├─ scripts/
│  └─ init_db.py
├─ src/
│  └─ autodraft/
│     ├─ main.py                 # FastAPI 엔트리
│     ├─ settings.py             # 환경변수 로딩
│     ├─ domain/
│     │  ├─ enums.py             # 상태(enum)
│     │  └─ policies.py          # 금칙어/마스킹/룰 기반 QA
│     ├─ schemas/
│     │  ├─ topic.py             # Topic 생성/응답 스키마
│     │  ├─ draft.py             # Draft 스키마
│     │  └─ pipeline.py          # run_selected 요청/응답
│     ├─ db/
│     │  ├─ session.py           # SQLAlchemy 엔진/세션
│     │  ├─ models.py            # Topic/Draft ORM
│     │  └─ repos.py             # 간단 CRUD
│     ├─ pipelines/
│     │  ├─ orchestrator.py      # Topic→Draft→QA→Export 순서
│     │  └─ steps/
│     │     ├─ topic_factory.py  # GPT로 주제 후보 생성
│     │     ├─ draft.py          # GPT로 초안 생성
│     │     ├─ quality_gate.py   # 룰 기반/LLM 기반 QA
│     │     └─ export.py         # HTML export 생성
│     ├─ integrations/
│     │  └─ llm/
│     │     └─ client.py         # LLM 호출 래퍼(모델 교체 지점)
│     ├─ prompts/
│     │  └─ v1/
│     │     ├─ topic_factory.md
│     │     ├─ draft.md
│     │     └─ qa.md
│     └─ templates/
│        └─ export_html/
│           └─ base.html         # 네이버 복붙용 HTML 템플릿
└─ exports/
   └─ (생성된 html 파일들)
```

> 데모 단계에서는 Celery/Redis/Playwright/Minio는 넣지 않습니다.
> “작동하는 세로 슬라이스”를 먼저 만든 뒤, 필요해지면 레시피1로 확장합니다.

---

## 환경 변수

`.env.example`

```env
# FastAPI
DEMO_API_TOKEN=change-me
DB_URL=sqlite:///./autodraft.db
EXPORT_DIR=./exports

# LLM
LLM_PROVIDER=openai
LLM_API_KEY=your-key
LLM_MODEL=gpt-4.1-mini
```

---

## Google Sheets 설정

### 1) 시트 탭 생성

* `Topics`
* `Drafts`

### 2) Topics 탭 컬럼(1행 헤더)

| topic_id | pillar | audience | title | angle | score | status | created_at | note |
| -------- | ------ | -------- | ----- | ----- | ----- | ------ | ---------- | ---- |

권장 드롭다운 값

* `pillar`: 공지, 학습법, 코테팁, 오답리포트, 후기, 학부모FAQ
* `audience`: 학생-초급, 학생-중급, 학부모, 일반
* `status`: NEW, SELECTED, REJECTED, DONE, ERROR

### 3) Drafts 탭 컬럼(1행 헤더)

| draft_id | topic_id | title | status | risk_score | summary | export_html_ref | last_error | updated_at |
| -------- | -------- | ----- | ------ | ---------- | ------- | --------------- | ---------- | ---------- |

`export_html_ref`는 **HTML 파일 경로 또는 URL(확장 시)** 를 저장합니다.

---

## Apps Script 설정(시트에서 버튼 2개 만들기)

### 개요

* 메뉴 `AutoDraft` 생성

  * `Generate Topics`
  * `Run Selected`

### Script Properties에 저장

* `BACKEND_BASE_URL` (예: `http://localhost:8000`)
* `DEMO_API_TOKEN`

### 동작 정의

* **Generate Topics**

  * 시트 상단의 설정 셀(예: `B2=pillar`, `C2=audience`, `D2=n`)을 읽어서
  * `POST /topics/generate` 호출
  * 응답으로 받은 topic들을 `Topics` 탭 아래에 append(status=NEW)

* **Run Selected**

  * `Topics.status == SELECTED` 인 행들의 `topic_id`를 모아
  * `POST /pipeline/run_selected` 호출
  * 결과를 `Drafts` 탭에 append
  * 처리 성공 시 Topics.status를 DONE(실패면 ERROR)

> 인증: Apps Script 요청에 `X-DEMO-TOKEN` 헤더로 `DEMO_API_TOKEN` 전송

---

## FastAPI 실행

### 1) 설치

(예: uv 사용 시)

```bash
uv venv
uv pip install -r requirements.txt
```

또는 poetry를 쓰는 경우 `pyproject.toml` 기반으로 설치.

### 2) DB 초기화

```bash
python scripts/init_db.py
```

### 3) 서버 실행

```bash
uvicorn autodraft.main:app --reload
```

Swagger: `http://localhost:8000/docs`

---

## API 계약(데모 최소)

### 1) Topic 생성

`POST /topics/generate`

**Request**

```json
{
  "pillar": "학습법",
  "audience": "학생-초급",
  "n": 10
}
```

**Response**

```json
{
  "items": [
    {
      "topic_id": "t_abc123",
      "title": "포인터가 헷갈리는 진짜 이유 3가지",
      "angle": "오해 유형 3가지 + 교정 루틴 + 연습문제",
      "score": 82
    }
  ]
}
```

### 2) 선택 토픽 실행(초안+QA+Export)

`POST /pipeline/run_selected`

**Request**

```json
{
  "topic_ids": ["t_abc123", "t_def456"]
}
```

**Response**

```json
{
  "drafts": [
    {
      "topic_id": "t_abc123",
      "draft_id": "d_001",
      "status": "EXPORTED",
      "risk_score": 18,
      "summary": "포인터 오해 3가지를 사례로 설명하고, 짧은 실습 루틴을 제시합니다.",
      "export_html_ref": "./exports/d_001.html"
    }
  ]
}
```

---

## TODO 체크리스트(구현 순서)

### Phase 1 — 시트/협업 UI(30분)

* [ ] Topics/Drafts 탭 생성
* [ ] 컬럼 헤더 구성
* [ ] pillar/audience/status 드롭다운 적용
* [ ] status=SELECTED 조건부서식 적용

### Phase 2 — 백엔드 “세로 슬라이스”(60~90분)

* [ ] FastAPI 프로젝트 스캐폴딩
* [ ] DB 모델(Topic, Draft) + session/repo
* [ ] 스키마(Pydantic) 고정: TopicIdea / DraftResult
* [ ] LLM client 래퍼(단일 함수로 시작)
* [ ] steps 구현:

  * [ ] topic_factory (JSON 출력 강제)
  * [ ] draft (JSON 또는 MD 생성)
  * [ ] quality_gate (룰 기반 risk_score)
  * [ ] export (HTML 파일 생성 + ref 반환)
* [ ] 엔드포인트 2개 구현:

  * [ ] `/topics/generate`
  * [ ] `/pipeline/run_selected`
* [ ] 데모용 토큰 인증(X-DEMO-TOKEN)

### Phase 3 — Apps Script 연결(30~60분)

* [ ] AutoDraft 메뉴 생성
* [ ] Generate Topics 구현(append to Topics)
* [ ] Run Selected 구현(append to Drafts + Topics 상태 업데이트)
* [ ] 에러 처리(toast + note 기록)

### Phase 4 — E2E 시연(15분)

* [ ] 시트에서 Generate Topics 실행 확인
* [ ] SELECTED 처리 후 Run Selected 확인
* [ ] export_html_ref로 HTML 열기/복사 테스트
* [ ] 네이버 붙여넣기 시 레이아웃 깨짐 여부 확인

---

## 다음 확장(레시피1로 자연스럽게)

* [ ] Celery/Redis 붙여서 비동기 + 재시도 + 로그 강화
* [ ] ResearchPack 도입(크롤링/요약/근거 캐시)
* [ ] LLM 기반 QA 추가(근거 없는 주장 표시, 민감표현 탐지)
* [ ] 이미지팩(prompt/alt/caption) 생성
* [ ] Export를 Minio/S3로 업로드하고 URL을 시트에 기록

---

## 운영 팁(데모에서 자주 생기는 문제)

* LLM 출력이 JSON을 깨면: **스키마 검증 실패 → 재시도(최대 2회)** 를 기본으로
* 시트 셀에 긴 HTML을 넣지 말고: **파일 저장 + 링크/경로만 기록**
* 상태 꼬임 방지: Run Selected는 **SELECTED만 처리 후 DONE/ERROR로 바꾸기**

