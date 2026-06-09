"""
16_build_and_run.py — Coordinator + Supervisor 멀티에이전트 그래프 (메인)

      ┌───────────┐
      │ Coordinator│   ← 사용자 입력 의도 분류
      └─────┬──────┘
            │ chitchat?  ─────── 직접 응답 → END
            └ info_query
            ▼
      ┌───────────────┐
      │ Supervisor    │   ← 라우팅 + generate + transform_query
      └──┬──┬──┬──┬───┘
         │  │  │  │
         ▼  ▼  ▼  ▼
    retrieve grade web_search   (3 개의 sub-agent)
         │  │  │
         └──┴──┘  → supervisor 로 복귀 (다음 행동 결정)

10_build_and_run.py 와의 차이:
  - retrieve / grade / web_search → *sub-agent* (책임 분리)
  - generate / transform_query   → *supervisor 의 내장 기능*
  - decide_to_generate / grade_generation → *supervisor_route* 로 통합 (조건부 라우팅)
  - 새로 등장: *Coordinator* 가 잡담을 supervisor 파이프라인 밖에서 흡수
"""
import importlib
import sys
from pathlib import Path
from typing import List, Optional, TypedDict

from langgraph.graph import StateGraph, START, END

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))     # supp/
sys.path.insert(0, str(Path(__file__).resolve().parent))             # supp_03/

# 숫자 시작 모듈은 importlib 로 우회
_sub = importlib.import_module("13_subagents")
_sup = importlib.import_module("14_supervisor")
_coord = importlib.import_module("15_coordinator")


# ─────────────────────────────────────────────────────────────
# 멀티에이전트 공유 State
# ─────────────────────────────────────────────────────────────
class MultiAgentState(TypedDict, total=False):
    user_input: str
    route: str                  # "chitchat" | "info_query"
    question: str               # 현재(재작성됐을 수 있는) 질문
    documents: List[str]
    web_search_needed: str      # "Yes" | "No"
    last_action: Optional[str]  # 어느 에이전트가 마지막에 일했는가
    next_agent: str             # supervisor 가 결정한 다음 행선지
    iteration: int
    answer: str                 # 최종 답변
    # 08_nodes.retrieve 가 retry_count 를 참조하기 때문에 호환용으로 보존
    retry_count: int


# ─────────────────────────────────────────────────────────────
# 그래프 조립
# ─────────────────────────────────────────────────────────────
def build_app():
    g = StateGraph(MultiAgentState)

    # === 노드 등록 ===
    g.add_node("coordinator",          _coord.coordinator)
    g.add_node("supervisor_route",     _sup.supervisor_route)
    g.add_node("supervisor_generate",  _sup.supervisor_generate)
    g.add_node("supervisor_transform", _sup.supervisor_transform)
    g.add_node("retrieve_agent",       _sub.retrieve_agent)
    g.add_node("grade_agent",          _sub.grade_agent)
    g.add_node("web_search_agent",     _sub.web_search_agent)

    # === 1. Coordinator 분기 ===
    g.add_edge(START, "coordinator")
    g.add_conditional_edges(
        "coordinator",
        _coord.coordinator_edge,
        {"end": END, "supervisor": "supervisor_route"},
    )

    # === 2. Supervisor → 다음 에이전트 라우팅 ===
    g.add_conditional_edges(
        "supervisor_route",
        _sup.supervisor_route_edge,
        {
            "retrieve_agent":       "retrieve_agent",
            "grade_agent":          "grade_agent",
            "web_search_agent":     "web_search_agent",
            "supervisor_generate":  "supervisor_generate",
            "supervisor_transform": "supervisor_transform",
            "done":                 END,
        },
    )

    # === 3. Sub-agent / supervisor 내부 노드 → 다시 supervisor_route 로 복귀 ===
    for node in ("retrieve_agent", "grade_agent", "web_search_agent",
                 "supervisor_transform", "supervisor_generate"):
        g.add_edge(node, "supervisor_route")

    return g.compile()


# ─────────────────────────────────────────────────────────────
# 실행 헬퍼
# ─────────────────────────────────────────────────────────────
def run_one(user_input: str) -> None:
    app = build_app()
    inputs = {"user_input": user_input, "iteration": 0, "retry_count": 0}

    print("\n" + "═" * 70)
    print(f"🚀 USER: {user_input}")
    print("═" * 70)

    final_state = None
    for output in app.stream(inputs, {"recursion_limit": 40}):
        for node, payload in output.items():
            final_state = {**(final_state or {}), **payload}
            # sub-agent / supervisor 함수 내부에서 이미 print 하므로 여기선 노드 표식만
            # (중복 출력을 피하려면 아래 한 줄을 주석 처리해도 됨)
            # print(f"  ▶ [{node}] 완료")

    print("\n📝 최종 답변")
    print("-" * 70)
    print((final_state or {}).get("answer", "(답변 없음)"))


# ─────────────────────────────────────────────────────────────
# 데모 3 종
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # ── 데모 1: 인사 (Coordinator 가 supervisor 우회) ──
    #     기대 트레이스:
    #       coordinator (chitchat) → END
    #     의의: supervisor 파이프라인 호출 0 회, 비용 절감
    run_one("안녕! 오늘 기분 어때?")

    # ── 데모 2: 사내문서로 답 가능 (Supervisor → retrieve → grade → generate) ──
    #     기대 트레이스:
    #       coordinator (info_query) → route(retrieve) → retrieve_agent →
    #       route(grade) → grade_agent → route(generate) → supervisor_generate →
    #       route(done) → END
    run_one("에이전트 메모리에는 어떤 종류가 있나?")

    # ── 데모 3: 사내문서 부족 → 웹 폴백 (Supervisor 가 transform + web_search 동원) ──
    #     기대 트레이스:
    #       coordinator → route(retrieve) → retrieve_agent → route(grade) → grade_agent →
    #       route(transform) → supervisor_transform → route(web_search) → web_search_agent →
    #       route(grade) → grade_agent → … → supervisor_generate → END
    run_one("오늘 비트코인 가격은 얼마인가?")
