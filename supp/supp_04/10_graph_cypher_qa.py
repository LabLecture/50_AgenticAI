"""
10_graph_cypher_qa.py — ★ 메인: 자연어 질문 → Cypher → 그래프 답변

GraphCypherQAChain 은 (1) LLM 이 스키마 보고 Cypher 생성 → (2) Neo4j 실행 → (3) LLM 이 결과를 자연어로 정리.

이 스크립트를 실행하기 전에 `python 08_load_to_neo4j.py` 가 먼저 돌아 있어야 그래프가 채워져 있다.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from langchain_neo4j import GraphCypherQAChain

from _common import get_llm, get_neo4j_graph, banner, llm_unavailable


QUESTIONS = [
    "Anthropic을 설립한 사람은 누구인가?",
    "Anthropic이 개발한 제품은?",
    "Anthropic 에 투자한 회사는?",
]


def main() -> None:
    banner("GraphCypherQAChain — 자연어 → Cypher → 답변")
    llm = get_llm()
    if llm is None:
        llm_unavailable()
        return

    graph = get_neo4j_graph()  # refresh_schema=True
    if graph is None:
        print("❌ NEO4J_* env 미설정")
        return

    chain = GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph,
        verbose=True,
        allow_dangerous_requests=True,  # LLM 생성 Cypher 의 임의 실행을 명시적으로 허용
    )

    for q in QUESTIONS:
        print("\n" + "─" * 70)
        print(f"❓ {q}")
        try:
            result = chain.invoke({"query": q})
            print(f"💬 {result['result']}")
        except Exception as e:
            print(f"⚠ {type(e).__name__}: {str(e)[:200]}")


if __name__ == "__main__":
    main()
