"""
06_crag_branch_logic.py — CRAG (Corrective RAG) 분기 로직 데모

LangGraph 없이 순수 함수로 CRAG 의 핵심 분기만 시뮬레이션:
  - 채점 통과 문서가 0 개   → web_search 로 폴백 (Incorrect)
  - 일부만 통과 / 보강 필요 → transform_query 후 재검색 (Ambiguous)
  - 충분히 통과              → generate (Correct)
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from typing import Literal, TypedDict, List

from _common import banner


class MockState(TypedDict):
    documents: List[str]
    needs_more_context: bool


def decide_after_grading(state: MockState) -> Literal["web_search", "transform_query", "generate"]:
    """채점 결과에 따라 다음 행동을 결정하는 라우터 함수."""
    relevant_docs = state["documents"]
    if len(relevant_docs) == 0:
        return "web_search"                  # Incorrect → 외부 폴백
    if state.get("needs_more_context"):
        return "transform_query"             # Ambiguous → 보강
    return "generate"                        # Correct  → 생성


def main() -> None:
    banner("CRAG 분기 로직 — 3 가지 시나리오")

    cases = [
        ("모든 문서 탈락 (Incorrect)",
         {"documents": [], "needs_more_context": False}),
        ("일부 통과 + 보강 필요 (Ambiguous)",
         {"documents": ["doc01 일부 통과"], "needs_more_context": True}),
        ("충분히 통과 (Correct)",
         {"documents": ["doc01", "doc02", "doc03"], "needs_more_context": False}),
    ]

    for label, state in cases:
        decision = decide_after_grading(state)
        print(f"  {label:<35} → {decision}")

    print("\n📝 핵심: 같은 '채점' 단계 뒤에서도 결과에 따라 3 갈래로 분기")
    print("   이 분기를 LangGraph 의 conditional edge 로 옮긴 것이 10_build_and_run.py")


if __name__ == "__main__":
    main()
