"""
08_load_to_neo4j.py — 추출한 GraphDocument 를 Neo4j 에 적재

baseEntityLabel=True  → 모든 노드에 공통 :__Entity__ 라벨 부여 (이후 인덱싱 편함)
include_source=True   → 원본 청크(:Document) 노드도 함께 저장해 출처 추적 가능

이 스크립트가 끝나면 Neo4j 안에 그래프가 살아 있어서 10_graph_cypher_qa.py 가 바로 활용한다.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer

from _common import get_llm, get_neo4j_graph, reset_neo4j, banner, llm_unavailable
from importlib import import_module
SAMPLE_TEXT = import_module("06_llm_graph_transformer").SAMPLE_TEXT


def main() -> None:
    banner("Neo4j 적재 — add_graph_documents")
    llm = get_llm()
    if llm is None:
        llm_unavailable()
        return

    graph = get_neo4j_graph(refresh_schema=False)
    if graph is None:
        print("❌ NEO4J_* env 미설정")
        return

    # 깨끗하게 시작
    reset_neo4j(graph)
    print("  (기존 그래프 전체 삭제)")

    transformer = LLMGraphTransformer(
        llm=llm,
        allowed_nodes=["Person", "Company", "Product"],
        allowed_relationships=["FOUNDED", "DEVELOPED", "INVESTED_IN", "WORKED_AT"],
        ignore_tool_usage=True,   # free 모델 호환
    )
    docs = [Document(page_content=SAMPLE_TEXT.strip())]
    graph_docs = transformer.convert_to_graph_documents(docs)

    graph.add_graph_documents(
        graph_docs,
        baseEntityLabel=True,
        include_source=True,
    )

    # 결과 확인
    labels = graph.query(
        "MATCH (n) RETURN labels(n) AS labels, count(*) AS cnt ORDER BY cnt DESC"
    )
    rels = graph.query(
        "MATCH ()-[r]->() RETURN type(r) AS rel, count(*) AS cnt ORDER BY cnt DESC"
    )
    print(f"\n📊 적재된 노드 라벨")
    for row in labels:
        print(f"  - {row['labels']}: {row['cnt']} 개")
    print(f"\n📊 적재된 관계 타입")
    for row in rels:
        print(f"  - {row['rel']}: {row['cnt']} 개")

    # refresh_schema 로 향후 GraphCypherQAChain 이 참고할 스키마 갱신
    graph.refresh_schema()
    print(f"\n📋 스키마 (refresh_schema 결과 발췌)")
    print(graph.schema[:400])


if __name__ == "__main__":
    main()
