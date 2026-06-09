"""
02_connect.py — Neo4j 연결 확인

.env 의 NEO4J_URI / NEO4J_USERNAME / NEO4J_PASSWORD 를 읽어 Neo4jGraph 인스턴스를 만들고,
간단한 Cypher 1 개를 실행해 응답을 확인한다.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from _common import get_neo4j_graph, banner


def main() -> None:
    banner("Neo4j 연결 확인")
    graph = get_neo4j_graph(refresh_schema=False)
    if graph is None:
        print("❌ NEO4J_* env 미설정. supp/.env 를 확인하세요.")
        return

    result = graph.query("RETURN 'Neo4j 연결 성공' AS msg, datetime() AS now")
    print(f"  ✅ {result[0]['msg']}")
    print(f"  서버 시각: {result[0]['now']}")

    # 현재 노드/관계 수
    counts = graph.query(
        "MATCH (n) WITH count(n) AS nodes "
        "OPTIONAL MATCH ()-[r]->() RETURN nodes, count(r) AS rels"
    )
    print(f"  현재 그래프: 노드 {counts[0]['nodes']}개 / 관계 {counts[0]['rels']}개")


if __name__ == "__main__":
    main()
