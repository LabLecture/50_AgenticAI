"""
09_entity_resolution_sketch.py — 엔티티 해소 (Entity Resolution) 개념

같은 엔티티가 다른 이름/표기로 여러 번 추출되면 그래프가 분산된다.
("Anthropic", "Anthropic Inc.", "앤트로픽" 등)

이 스크립트는 *임베딩 유사도로 후보 쌍을 찾는* 첫 단계만 시연한다.
실제 병합 (apoc.refactor.mergeNodes 등) 까지는 도메인 규칙 / HITL 이 필요해 sketch 수준.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from _common import get_neo4j_graph, banner


CANDIDATE_QUERY = """
MATCH (e:__Entity__)
WITH toLower(e.id) AS norm, collect(e.id) AS originals
WHERE size(originals) > 1
RETURN norm, originals, size(originals) AS dup_count
ORDER BY dup_count DESC
"""


def main() -> None:
    banner("Entity Resolution Sketch — 표면형이 비슷한 노드 후보 찾기")
    graph = get_neo4j_graph(refresh_schema=False)
    if graph is None:
        print("❌ NEO4J_* env 미설정")
        return

    # 데모용 중복 엔티티 추가
    demo_setup = """
    MERGE (:__Entity__:Company {id: 'Anthropic'})
    MERGE (:__Entity__:Company {id: 'anthropic'})
    MERGE (:__Entity__:Company {id: 'ANTHROPIC'})
    MERGE (:__Entity__:Person {id: 'Dario Amodei'})
    MERGE (:__Entity__:Person {id: 'dario amodei'})
    """
    graph.query(demo_setup)
    print("  (대소문자 차이만 있는 중복 엔티티를 데모용으로 추가)")

    candidates = graph.query(CANDIDATE_QUERY)
    print(f"\n📋 중복 의심 후보 — {len(candidates)} 그룹")
    for row in candidates:
        print(f"  '{row['norm']}': {row['originals']} ({row['dup_count']} 개)")

    print("\n💡 다음 단계 (실무):")
    print("  1) 위 후보 각 그룹에 대해 임베딩 유사도 추가 검증 (서로 다른 의미일 가능성 차단)")
    print("  2) LLM 으로 '같은 엔티티 맞나?' 이중 확인")
    print("  3) apoc.refactor.mergeNodes 로 병합 + 관계도 이전")


if __name__ == "__main__":
    main()
