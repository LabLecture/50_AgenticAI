"""
11_cypher_with_examples.py — few-shot 예시로 Cypher 생성 품질 향상

질문-Cypher 페어를 프롬프트에 넣으면 LLM 이 패턴을 학습해 정확도가 오른다.
GraphCypherQAChain.from_llm 은 cypher_prompt 인자로 커스텀 프롬프트를 받을 수 있다.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from langchain_core.prompts import PromptTemplate
from langchain_neo4j import GraphCypherQAChain

from _common import get_llm, get_neo4j_graph, banner, llm_unavailable


# PromptTemplate 은 {} 를 변수로 인식. Cypher 의 {id:'X'} 와 충돌하므로 {{ }} 로 escape.
CYPHER_EXAMPLES = """
질문: X 를 설립한 사람은?
Cypher: MATCH (p:Person)-[:FOUNDED]->(c:Company {{id:'X'}}) RETURN p.id

질문: X 에 투자한 회사는?
Cypher: MATCH (i:Company)-[:INVESTED_IN]->(c:Company {{id:'X'}}) RETURN i.id

질문: X 가 개발한 제품은?
Cypher: MATCH (c:Company {{id:'X'}})-[:DEVELOPED]->(p:Product) RETURN p.id
"""

CUSTOM_PROMPT = PromptTemplate.from_template(
    """다음 Neo4j 그래프 스키마를 보고 사용자 질문에 답하는 Cypher 만 출력하라.
설명·코드펜스 금지. 결과는 반드시 RETURN 절을 포함한다.

스키마:
{schema}

참고 예시:
""" + CYPHER_EXAMPLES + """

질문: {question}
Cypher:"""
)


def main() -> None:
    banner("Few-shot Cypher 프롬프트")
    llm = get_llm()
    if llm is None:
        llm_unavailable()
        return

    graph = get_neo4j_graph()
    if graph is None:
        print("❌ NEO4J_* env 미설정")
        return

    chain = GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph,
        cypher_prompt=CUSTOM_PROMPT,
        verbose=True,
        allow_dangerous_requests=True,
    )

    question = "Anthropic 을 설립한 사람과 그가 일했던 회사를 알려줘"
    print(f"\n❓ {question}")
    try:
        result = chain.invoke({"query": question})
        print(f"💬 {result['result']}")
    except Exception as e:
        print(f"⚠ {type(e).__name__}: {str(e)[:200]}")


if __name__ == "__main__":
    main()
