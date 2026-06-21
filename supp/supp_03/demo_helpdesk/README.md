# 종합 데모 A-1 · 사내 헬프데스크 에이전트

규정 문서 RAG × 사내 DB(PostgreSQL) × 멀티턴 슬롯필링을 한 LangGraph 로 묶은 **실전 데모**.
supp_03 단편 실습(라우터·분해·채점·CRAG·그래프 조립)의 종합편이다.

## 구조

```
👤 질문 → ingest(슬롯필링 응답 감지)
            └→ router ─┬─ db_agent   : PostgreSQL 조회 (사번 없으면 되묻기)
                       ├─ retrieve → grade ─┬─ generate     (근거 인용 답변)
                       │                    ├─ rewrite ↺    (최대 2회 재검색)
                       │                    └─ no_evidence  (정직한 "근거 없음")
                       └─ hybrid    : 질문 분해 → 규정 + DB 종합
```

- 회사: 가상 기업 **(주)다희** — `data/` 규정 md 3종 (취업규칙·복무규정·경비처리지침)
- DB: `employees` / `leaves` / `expenses` — 데모 주인공 E1003 김민준 (잔여 연차 12일)
- LLM: OpenRouter (supp/.env 의 `OPENROUTER_API_KEY`), 임베딩: e5-small 로컬

## 실행 순서

```powershell
# 0) PostgreSQL 컨테이너 (1회)
docker run -d --name helpdesk-pg `
  -e POSTGRES_USER=demo -e POSTGRES_PASSWORD=demo1234 -e POSTGRES_DB=helpdesk `
  -p 5433:5432 postgres:16-alpine

# 1) supp venv 로 시드 + 데모  (supp/supp_03/demo_helpdesk 에서)
..\..\venv\Scripts\python.exe 01_seed_db.py     # 테이블 생성 + 시드 + 검증
..\..\venv\Scripts\python.exe 03_run_demo.py    # 5턴 시나리오 헤드리스 실행

# 2) (선택) 챗 UI 로 시연 — supp_08 프론트 재사용
..\..\venv\Scripts\python.exe -m uvicorn 04_api:app --port 8001
# 별도 터미널: cd test\chat-frontend && npm start   (→ localhost:3000)
```

## 데모 스토리 (5턴)

| # | 발화 | 시연 포인트 |
|---|------|------------|
| 1 | 연차가 며칠 남았어요? | router→db, 사번 없음 → **슬롯필링** 되묻기 |
| 2 | E1003 이요 | 슬롯 채움 → 원래 질문 자동 재개 → **DB 조회** 잔여 12일 |
| 3 | 연차 이월은 어떻게 되나요? | router→doc, 조항 검색·채점 → **근거 인용** (취업규칙 §12) |
| 4 | 작년에 이월한 연차도 올해 쓸 수 있어요? | router→**hybrid**, 분해 → 규정(6/30 기한)+내 이월 3일 종합 |
| 5 | 주4일제는 언제 도입되나요? | grade 불합격 → rewrite ×2 → **CRAG 정직 응답** (환각 방지) |

## supp_03 실습 재사용 매핑

| 단편 실습 | 이 데모에서 |
|---|---|
| 02_query_router | `router` 노드 (db/doc/hybrid 3분기로 확장) |
| 03_query_decomposition | `hybrid` 노드의 질문 분해 |
| 04_retrieval_grader | `grade` 노드 |
| 05_crag_branch_logic | `rewrite` 루프 + `no_evidence` 분기 |
| 06~10 State·노드·엣지 | 그래프 골격 + MemorySaver 멀티턴 |

## 설계 메모

- **SQL 은 LLM 이 직접 쓰지 않는다** — LLM 은 intent 만 분류하고 SQL 은 코드의 템플릿
  (`SQL_TEMPLATES`)을 쓴다. 데모 안정성 + SQL 인젝션 방지의 실무 패턴.
- **TODAY 고정(2026-06-13)** — 4턴의 "이월분 6/30 까지 → 17일 남음" 시연 재현성.
- 규정 청킹은 글자수가 아니라 **조항(제n조) 단위** — 규정류 문서의 정석.
