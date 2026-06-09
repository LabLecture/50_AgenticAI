"""
05_neo4j_vector.py — Neo4j 벡터 인덱스

문서 청크를 :Chunk 노드로 저장하면서 임베딩까지 함께 인덱싱.
그래프 DB 위에 벡터 RAG 와 같은 유사도 검색이 얹힌다.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import os

from langchain_core.documents import Document

from _common import get_embeddings, banner


def main() -> None:
    banner("Neo4j 벡터 인덱스 — 문서 청크 임베딩 저장 + 유사도 검색")
    if not os.getenv("NEO4J_URI"):
        print("❌ NEO4J_* env 미설정")
        return

    from langchain_neo4j import Neo4jVector

    docs = [
        Document(page_content="LLM 에이전트의 메모리는 단기·장기·감각으로 나뉜다."),
        Document(page_content="도구 사용은 LLM 에이전트가 외부 API 를 호출하는 능력이다."),
        Document(page_content="CRAG 는 벡터 검색 결과의 신뢰도를 평가해 웹 폴백으로 분기한다."),
        Document(page_content="LangGraph 는 상태 머신으로 멀티 에이전트 워크플로우를 표현한다."),
    ]

    # 기존 인덱스가 남아 있을 수 있으니 새 컬렉션 이름 사용
    vector_index = Neo4jVector.from_documents(
        documents=docs,
        embedding=get_embeddings(),
        url=os.environ["NEO4J_URI"],
        username=os.environ["NEO4J_USERNAME"],
        password=os.environ["NEO4J_PASSWORD"],
        index_name="document_chunks",
        node_label="Chunk",
    )
    print(f"  ✅ Chunk 노드 + 벡터 인덱스 'document_chunks' 생성")

    query = "에이전트가 외부 API 를 쓰는 방법은?"
    results = vector_index.similarity_search(query, k=3)
    print(f"\n🔍 query: {query!r}")
    for i, d in enumerate(results, 1):
        print(f"  {i}. {d.page_content}")


if __name__ == "__main__":
    main()
