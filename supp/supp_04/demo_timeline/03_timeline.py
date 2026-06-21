"""
03_timeline.py — "사건을 시간순으로 정리해줘" (벤치마크 데모 ②의 재현).

그래프에서 Event 를 날짜순으로 뽑고(EVIDENCED_BY 로 출처 문서 연결),
LLM 이 출처 표기가 달린 타임라인 서술을 생성한다.

핵심: 타임라인의 **정렬·집계는 Cypher(결정론)** 가 하고,
LLM 은 **서술만** 담당한다 — 날짜가 꼬이는 환각이 구조적으로 차단된다.
"""
from _demo_common import get_llm, get_neo4j_graph, banner, CASE_ID


def fetch_timeline(graph) -> list[dict]:
    # 같은 사건(date+type+amount)을 여러 문서가 증거할 수 있다 → 출처를 묶는다
    return graph.query("""
        MATCH (e:Event {case: $c})-[:EVIDENCED_BY]->(d:Document)
        WITH e.date AS date, e.type AS type, e.amount AS amount,
             collect(DISTINCT d.doc_id) AS sources,
             head(collect(e.summary)) AS summary
        RETURN toString(date) AS date, type, amount, summary, sources
        ORDER BY date""", params={"c": CASE_ID})


def main() -> None:
    banner("사건 타임라인 생성 — Cypher 정렬 + LLM 서술")
    graph = get_neo4j_graph(refresh_schema=False)
    llm = get_llm()
    if graph is None or llm is None:
        print("❌ env 미설정"); return

    rows = fetch_timeline(graph)
    print(f"  그래프에서 이벤트 {len(rows)}건 (날짜순):\n")
    for r in rows:
        amt = f" {r['amount']:,}원" if r["amount"] else ""
        print(f"   {r['date']}  [{r['type']}]{amt}  ← {','.join(r['sources'])}")

    facts = "\n".join(
        f"- {r['date']} | {r['type']} | {r['amount'] or '-'} | {r['summary']} "
        f"| 출처: {','.join(r['sources'])}" for r in rows)

    narrative = llm.invoke(
        [("system", "법률 사무 보조자. 아래 사실관계(이미 시간순 정렬됨)만으로 사건 경과를 "
                     "마크다운 타임라인으로 정리하라. 각 항목 끝에 출처를 (doc_id) 형식으로 "
                     "반드시 표기. 마지막에 '결론' 2~3문장: 분쟁의 핵심 쟁점과 현재 상태. "
                     "사실관계에 없는 내용 추가 금지."),
         ("user", f"사건: 재고관리시스템 공급계약(CT-2025-017) 대금 분쟁\n\n{facts}")]).content

    print("\n" + "═" * 70)
    print("📜 LLM 타임라인 서술:\n")
    print(narrative)


if __name__ == "__main__":
    main()
