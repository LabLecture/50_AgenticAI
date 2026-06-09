"""
12_hybrid_retrieval.py — 하이브리드 검색: 벡터 진입 + 그래프 확장

전략:
  (1) 질문을 임베딩해 :Entity__ 노드 중 가장 비슷한 진입점을 찾는다 (벡터)
  (2) 그 진입점에서 1 홉 이웃을 따라가 추가 컨텍스트를 모은다 (그래프)
  (3) 벡터 진입점 + 그래프 이웃을 합쳐 컨텍스트로 사용

→ "의미적으로 가까운 것" + "구조적으로 연결된 것" 을 동시에 활용
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import os

from _common import get_embeddings, get_neo4j_graph, banner


def main() -> None:
    banner("하이브리드 검색 — 벡터 진입 + 그래프 1홉 확장")
    graph = get_neo4j_graph(refresh_schema=False)
    if graph is None:
        print("❌ NEO4J_* env 미설정")
        return

    from langchain_neo4j import Neo4jVector

    # 적재된 그래프 위에 entity_index 벡터 인덱스 얹기
    entity_index = Neo4jVector.from_existing_graph(
        embedding=get_embeddings(),
        url=os.environ["NEO4J_URI"],
        username=os.environ["NEO4J_USERNAME"],
        password=os.environ["NEO4J_PASSWORD"],
        index_name="entity_index",
        node_label="__Entity__",
        text_node_properties=["id"],
        embedding_node_property="embedding",
    )
    print("  ✅ entity_index 벡터 인덱스 준비")

    question = "Claude 와 관련된 사람·회사·제품은?"
    print(f"\n🔍 query: {question!r}")

    # (1) 벡터 진입점
    seeds = entity_index.similarity_search(question, k=3)
    print(f"\n[Step 1] 벡터 진입점 Top-3")
    for s in seeds:
        print(f"  - {s.page_content[:80]}")

    # (2) 그래프 1 홉 확장
    expand_q = """
    MATCH (e:__Entity__)-[r]-(neighbor:__Entity__)
    WHERE e.id = $entity_id
    RETURN type(r) AS rel, neighbor.id AS neighbor, labels(neighbor) AS labels
    LIMIT 10
    """
    seen = set()
    print(f"\n[Step 2] 각 진입점에서 1 홉 이웃")
    for s in seeds:
        # text_node_properties=['id'] 이면 page_content 가 "\nid: <값>" 이라 추출 필요
        pc = s.page_content.strip()
        entity_id = pc.split(":", 1)[-1].strip().splitlines()[0].strip()
        if entity_id in seen:
            continue
        seen.add(entity_id)
        neighbors = graph.query(expand_q, params={"entity_id": entity_id})
        print(f"\n  ▶ seed=({entity_id})")
        for n in neighbors:
            print(f"     -[:{n['rel']}]-> ({n['neighbor']}, {n['labels']})")


if __name__ == "__main__":
    main()
