"""
04_qa_text2cypher.py — 자연어 → Cypher 질의응답 (few-shot 필수).

supp_04/11 의 few-shot 패턴 재사용. 질문 3종:
  Q1 집계: 한빛유통이 다온소프트에 지급한 총액
  Q2 추적: 다온소프트가 보낸 내용증명 목록
  Q3 멀티홉 킬러: 피고 회사 직원 중 계약서에 서명하지 않은 사람 (→ 이수진)
     → 벡터 RAG 로는 어려운 부정(NOT)+집합 연산 질의
"""
from langchain_core.prompts import PromptTemplate
from langchain_neo4j import GraphCypherQAChain

from _demo_common import get_llm, get_neo4j_graph, banner, CASE_ID

# PromptTemplate 의 { } 충돌 → Cypher 중괄호는 {{ }} 로 escape.
# (f-string 을 쓰면 {{ }} 가 한 번 소비돼 PromptTemplate 가 변수로 오인한다 — 일반 문자열 유지!)
CYPHER_EXAMPLES = """
질문: 한빛유통이 다온소프트에 지급한 금액의 합계는?
Cypher: MATCH (:Party {{name:'한빛유통', case:'CT-2025-017'}})-[p:PAID]->(:Party {{name:'다온소프트'}}) RETURN sum(p.amount) AS total

질문: 다온소프트 측이 발송한 내용증명은 몇 건이고 언제인가?
Cypher: MATCH (s:Party {{case:'CT-2025-017'}})-[:WORKS_FOR]->(:Party {{name:'다온소프트'}}), (s)-[:SENT]->(d:Document) WHERE d.title CONTAINS '내용증명' RETURN d.doc_id, toString(d.date) AS date ORDER BY d.date

질문: 한빛유통 소속 인물 중 계약서에 서명하지 않은 사람은?
Cypher: MATCH (p:Party {{kind:'person', case:'CT-2025-017'}})-[:WORKS_FOR]->(:Party {{name:'한빛유통'}}) WHERE NOT (p)-[:SIGNED]->(:Contract) RETURN p.name
"""

CUSTOM_PROMPT = PromptTemplate.from_template(
    """다음 Neo4j 스키마를 보고 질문에 답하는 Cypher 만 출력하라. 설명·코드펜스 금지.
모든 노드에 case 프로퍼티가 있다: 반드시 case:'""" + CASE_ID + """' 조건을 포함하라.
이 사건의 Contract 노드는 하나뿐이다 — Contract 에는 title 등 다른 속성 필터를 붙이지 마라.

스키마:
{schema}

참고 예시:
""" + CYPHER_EXAMPLES + """

질문: {question}
Cypher:""")

QUESTIONS = [
    "한빛유통이 다온소프트에 지급한 돈은 모두 합쳐 얼마인가?",
    "다온소프트가 발송한 내용증명을 날짜순으로 알려줘.",
    "한빛유통 직원 가운데 공급계약서에 서명하지 않은 사람이 있나? 있다면 누구이고 직책은?",
]


def main() -> None:
    banner("Text2Cypher QA — few-shot")
    llm = get_llm()
    graph = get_neo4j_graph()   # refresh_schema=True → {schema} 채움
    if llm is None or graph is None:
        print("❌ env 미설정"); return

    # return_intermediate_steps=True → 생성된 Cypher 와 그래프 원본 결과를 노출.
    # 데모에서 "Cypher 와 조회 결과가 곧 사실"임을 보여준다 — NL 답변은 free 모델
    # 사정으로 흔들릴 수 있으나, 그 위 두 줄(Cypher·결과)이 결정론적 근거다.
    chain = GraphCypherQAChain.from_llm(
        llm=llm, graph=graph, cypher_prompt=CUSTOM_PROMPT,
        verbose=False, allow_dangerous_requests=True,
        return_intermediate_steps=True,
    )
    for i, q in enumerate(QUESTIONS, 1):
        print(f"\n{'─' * 70}\n❓ Q{i}. {q}")
        try:
            result = chain.invoke({"query": q})
            steps = result.get("intermediate_steps", [])
            cypher = next((s["query"] for s in steps if "query" in s), "")
            context = next((s["context"] for s in steps if "context" in s), [])
            if cypher:
                print(f"  🔧 Cypher: {cypher.strip()}")
            print(f"  📊 결과:   {context}")
            print(f"  💬 답변:   {result['result']}")
        except Exception as e:
            print(f"  ⚠ 실패: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
