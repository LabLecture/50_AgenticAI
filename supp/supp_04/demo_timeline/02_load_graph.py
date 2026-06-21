"""
02_load_graph.py — extracted.json → Neo4j 결정론적 MERGE 적재.

스키마 (시나리오안 B-1):
  (:Party {name, kind, case})            kind: person|company
  (:Contract {id, date, amount, case})
  (:Event {type, date, amount, summary, case})
  (:Document {doc_id, title, date, text, case})
  (person)-[:WORKS_FOR]->(company)
  (party)-[:SIGNED]->(contract)
  (company)-[:PAID {amount, date}]->(company)
  (event)-[:REFERS_TO]->(contract)
  (event)-[:EVIDENCED_BY]->(document)
  (party)-[:SENT]->(document)   (party)-[:RECEIVED]->(document)

LLM 추출(01)과 적재(02)를 분리하는 이유: 추출 결과를 사람이 extracted.json 에서
검수·수정한 뒤 재적재할 수 있다 — 실제 프로젝트의 휴먼인더루프 지점.
"""
import json

from _demo_common import (
    get_neo4j_graph, reset_demo_graph, load_docs, banner, EXTRACT_JSON, CASE_ID,
)


def main() -> None:
    banner("Neo4j 적재 — 사건 그래프")
    graph = get_neo4j_graph(refresh_schema=False)
    if graph is None:
        print("❌ NEO4J_* env 미설정"); return
    if not EXTRACT_JSON.exists():
        print("❌ extracted.json 없음 — 01_extract.py 먼저 실행"); return

    ext = json.loads(EXTRACT_JSON.read_text(encoding="utf-8"))
    docs = {d["doc_id"]: d for d in load_docs()}

    reset_demo_graph(graph)
    print(f"  기존 데모 노드 삭제 (case={CASE_ID})")

    # 1) 계약 노드 (doc01 기준 고정 값 — 계약서가 원천)
    graph.query("""
        MERGE (c:Contract {id: $id, case: $case})
        SET c.date = date('2025-11-20'), c.amount = 120000000,
            c.title = '재고관리시스템 구축'""", params={"id": CASE_ID, "case": CASE_ID})

    for doc_id, r in ext.items():
        # 2) Document 노드 (원문 보관 → 출처 링크의 근거)
        graph.query("""
            MERGE (d:Document {doc_id: $doc_id, case: $case})
            SET d.title = $title, d.date = date($date), d.text = $text""",
            params={"doc_id": doc_id, "case": CASE_ID,
                    "title": docs[doc_id]["title"],
                    "date": r["doc_date"], "text": docs[doc_id]["text"]})

        # 3) 인물·회사 Party + WORKS_FOR
        for p in r["persons"]:
            graph.query("""
                MERGE (per:Party {name: $name, case: $case})
                SET per.kind = 'person', per.title = $title
                MERGE (co:Party {name: $company, case: $case})
                SET co.kind = 'company'
                MERGE (per)-[:WORKS_FOR]->(co)""",
                params={"name": p["name"], "title": p["title"],
                        "company": p["company"], "case": CASE_ID})

        # 4) 서명 (계약서만)
        for s in r.get("signers", []):
            graph.query("""
                MATCH (p:Party {name: $name, case: $case})
                MATCH (c:Contract {id: $cid, case: $case})
                MERGE (p)-[:SIGNED]->(c)""",
                params={"name": s, "cid": CASE_ID, "case": CASE_ID})

        # 5) 발신/수신
        for key, rel in (("sender_person", "SENT"), ("receiver_person", "RECEIVED")):
            if r.get(key):
                graph.query(f"""
                    MATCH (p:Party {{name: $name, case: $case}})
                    MATCH (d:Document {{doc_id: $doc_id, case: $case}})
                    MERGE (p)-[:{rel}]->(d)""",
                    params={"name": r[key], "doc_id": doc_id, "case": CASE_ID})

        # 6) 이벤트 + 증거 링크 + 지급 관계
        for ev in r["events"]:
            graph.query("""
                MERGE (e:Event {type: $type, date: date($date), case: $case,
                                doc_id: $doc_id})
                SET e.amount = $amount, e.summary = $summary
                WITH e
                MATCH (c:Contract {id: $cid, case: $case})  MERGE (e)-[:REFERS_TO]->(c)
                WITH e
                MATCH (d:Document {doc_id: $doc_id, case: $case})
                MERGE (e)-[:EVIDENCED_BY]->(d)""",
                params={"type": ev["type"], "date": ev["date"], "case": CASE_ID,
                        "amount": ev.get("amount"), "summary": ev["summary"],
                        "doc_id": doc_id, "cid": CASE_ID})
            if ev["type"] == "지급" and ev.get("amount") and ev.get("from_company"):
                # MERGE 키에 date+amount 포함 → 같은 입금을 여러 문서가
                # 언급해도 PAID 관계는 1개 (중복 집계 방지)
                graph.query("""
                    MERGE (f:Party {name: $f, case: $case}) SET f.kind='company'
                    MERGE (t:Party {name: $t, case: $case}) SET t.kind='company'
                    MERGE (f)-[p:PAID {date: date($date), amount: $amount,
                                       case: $case}]->(t)""",
                    params={"f": ev["from_company"], "t": ev["to_company"] or "다온소프트",
                            "date": ev["date"], "amount": ev["amount"], "case": CASE_ID})

    # ── 적재 결과 요약 ────────────────────────────────────────────────
    stats = graph.query("""
        MATCH (n {case: $c})
        RETURN labels(n)[0] AS label, count(*) AS cnt ORDER BY label""",
        params={"c": CASE_ID})
    print("\n  📊 적재 결과:")
    for row in stats:
        print(f"     {row['label']:<10} {row['cnt']}개")
    paid = graph.query("""
        MATCH ({case:$c})-[p:PAID]->({case:$c}) RETURN sum(p.amount) AS total""",
        params={"c": CASE_ID})
    print(f"     PAID 총액   {paid[0]['total']:,}원 "
          f"{'✅' if paid[0]['total'] == 56_000_000 else '⚠'}")
    print("\n  → Neo4j Browser(http://localhost:7474)에서 시각화:")
    print(f"     MATCH p=(n {{case:'{CASE_ID}'}})-[r]-() RETURN p")


if __name__ == "__main__":
    main()
