"""
13_compare_vector_vs_graph.py — Vector RAG vs GraphRAG 정성 비교

같은 질문 4 종을 두 방식에 던져 결과 차이를 *체감* 한다.
질문 유형:
  - local_fact   : 둘 다 잘함
  - multi_hop    : GraphRAG 우위
  - global       : GraphRAG 우위 (요약 종합)
  - aggregation  : 벡터 RAG 불가 (관계 개수 집계)
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_neo4j import GraphCypherQAChain, Neo4jVector

from _common import get_llm, get_embeddings, get_neo4j_graph, banner, llm_unavailable

import os


QUESTIONS = {
    "local_fact":   "Claude 를 개발한 회사는?",
    "multi_hop":    "Anthropic 의 설립자가 이전에 일했던 회사는?",
    "global":       "이 그래프에 등장하는 핵심 조직 / 인물을 정리해줘.",
    "aggregation":  "가장 많은 관계를 가진 엔티티는?",
}


def main() -> None:
    banner("Vector RAG vs GraphRAG — 같은 질문, 다른 결과")
    llm = get_llm()
    if llm is None:
        llm_unavailable()
        return

    graph = get_neo4j_graph()
    if graph is None:
        print("❌ NEO4J_* env 미설정")
        return

    # Vector RAG: Neo4jVector(document_chunks) 위에서 유사도 검색 + LLM
    chunk_index = Neo4jVector.from_existing_index(
        embedding=get_embeddings(),
        url=os.environ["NEO4J_URI"],
        username=os.environ["NEO4J_USERNAME"],
        password=os.environ["NEO4J_PASSWORD"],
        index_name="document_chunks",  # 08 단계에서 include_source=True 로 생성된 :Document 노드 활용
    )
    rag_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "다음 컨텍스트만 근거로 한국어로 간결히 답하라. 모르면 모른다고 하라.\n\n{context}"),
        ("human", "{question}"),
    ])
    rag_chain = rag_prompt | llm | StrOutputParser()

    def run_vector(q: str) -> str:
        docs = chunk_index.similarity_search(q, k=3)
        ctx = "\n\n".join(d.page_content for d in docs) or "(검색 결과 없음)"
        return rag_chain.invoke({"context": ctx, "question": q})

    # GraphRAG: GraphCypherQAChain
    graph_chain = GraphCypherQAChain.from_llm(
        llm=llm, graph=graph, verbose=False, allow_dangerous_requests=True,
    )

    def run_graph(q: str) -> str:
        try:
            return graph_chain.invoke({"query": q})["result"]
        except Exception as e:
            return f"[ERROR {type(e).__name__}: {str(e)[:80]}]"

    for label, q in QUESTIONS.items():
        print("\n" + "═" * 70)
        print(f"📌 [{label}] {q}")
        print("─" * 70)
        print(f"  Vector RAG: {run_vector(q)[:300]}")
        print()
        print(f"  Graph  RAG: {run_graph(q)[:300]}")


if __name__ == "__main__":
    main()
