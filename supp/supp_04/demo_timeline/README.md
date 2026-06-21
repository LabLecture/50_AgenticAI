# 종합 데모 B-1 · 계약 분쟁 타임라인 분석기

사건 문서 묶음 → 지식그래프 자동 구축 → 시간순 타임라인 + Text2Cypher QA.
supp_04 단편 실습(추출·적재·Text2Cypher·비교)의 종합편이자,
"법률 문서 타임라인 정리" 데모의 GraphRAG 버전이다.

## 사건 개요 (가상)

재고관리시스템 공급계약(CT-2025-017, 1.2억) 대금 분쟁:
**다온소프트**(공급, 대표 김재현) vs **한빛유통**(발주, 대표 박성호 / 구매팀장 이수진).
계약금 3,600만 입금 → 중도금 4,800만 미지급 → 내용증명 3차례 ↔ 회신 2차례
→ 부분 입금 2,000만 → 분할 지급 제안 (현재 상태). 문서 8건이 `data/` 에 있다.

## 그래프 스키마

```
(:Party {name, kind, title})   (:Contract {id, date, amount})
(:Event {type, date, amount, summary})   (:Document {doc_id, title, date, text})
(person)-[:WORKS_FOR]->(company)      (party)-[:SIGNED]->(contract)
(company)-[:PAID {amount, date}]->(company)
(event)-[:REFERS_TO]->(contract)      (event)-[:EVIDENCED_BY]->(document)
(party)-[:SENT]->(document)           (party)-[:RECEIVED]->(document)
```

모든 노드에 `case='CT-2025-017'` — 같은 Neo4j 의 다른 실습 데이터와 격리.

## 실행 순서

```powershell
docker start neo4j-graphrag        # supp_04 의 Neo4j 재기동 (~30초)

# supp/supp_04/demo_timeline 에서, supp venv 사용
..\..\venv\Scripts\python.exe 01_extract.py          # LLM 구조화 추출 → extracted.json
..\..\venv\Scripts\python.exe 02_load_graph.py       # 결정론적 MERGE 적재 + 검증
..\..\venv\Scripts\python.exe 03_timeline.py         # 타임라인 생성 (데모 장면 1)
..\..\venv\Scripts\python.exe 04_qa_text2cypher.py   # 자연어 QA 3종 (데모 장면 2)
..\..\venv\Scripts\python.exe 05_compare_vector.py   # 벡터 vs 그래프 비교 (데모 장면 3)
```

Neo4j Browser(http://localhost:7474, neo4j/test1234) 시각화:
`MATCH p=(n {case:'CT-2025-017'})-[r]-() RETURN p`

## 데모 장면

| # | 장면 | 보여주는 것 |
|---|------|------------|
| 0 | Browser 그래프 시각화 | "문서 더미가 그림이 됐다" |
| 1 | "사건을 시간순으로 정리해줘" | Cypher 정렬 + LLM 서술, **항목마다 출처(doc_id)** |
| 2 | "지급 총액은?" / "내용증명 목록은?" | Text2Cypher (few-shot) 집계·추적 |
| 3 | "한빛유통 직원 중 미서명자는?" | 벡터 RAG(불안정) vs 그래프(이수진, 결정론) |

## supp_04 실습 재사용 매핑

| 단편 실습 | 이 데모에서 |
|---|---|
| 06·07 (스키마 제약 추출) | 01_extract — Pydantic 구조화 출력으로 발전 |
| 08 (Neo4j 적재) | 02_load_graph — MERGE + case 격리 |
| 10·11 (Text2Cypher + few-shot) | 04_qa — few-shot 예시 3종 |
| 13 (벡터 vs 그래프 비교) | 05_compare — 집합 연산 킬러 질문 |

## 설계 메모

- **추출(LLM)과 적재(코드)를 분리** — extracted.json 을 사람이 검수·수정 후 재적재
  가능. 실제 프로젝트의 휴먼인더루프 지점.
- LLMGraphTransformer 대신 **Pydantic 구조화 출력**을 쓴 이유: 이 도메인은 이벤트의
  date/amount 프로퍼티가 핵심인데 LLMGraphTransformer 는 프로퍼티 추출이 약하다.
- **타임라인의 정렬·집계는 Cypher, LLM 은 서술만** — 날짜 환각이 구조적으로 차단됨.
- 검증 기준값: PAID 총액 5,600만 원 / 계약서 서명인 {김재현, 박성호} / 미서명 직원 이수진.
