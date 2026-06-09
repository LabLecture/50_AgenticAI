"""
10_build_and_run.py — 자기교정형 Agentic RAG 그래프 조립 + 실행 (메인)

흐름:
  retrieve → grade_documents
            ├ (관련 있음) → generate → (충실성/유용성)
            │                            ├ 통과 → END
            │                            ├ 환각 → generate 재시도
            │                            └ 미흡 → transform_query → web_search → grade_documents (순환)
            └ (관련 없음) → transform_query → web_search → grade_documents (순환)
"""
import importlib
import sys
from pathlib import Path
from typing import List, TypedDict

from langgraph.graph import StateGraph, START, END

# 숫자로 시작하는 08_nodes.py / 09_conditional_edges.py 는 일반 import 불가 → importlib 로 우회
sys.path.insert(0, str(Path(__file__).resolve().parent))
_nodes = importlib.import_module("08_nodes")
_edges = importlib.import_module("09_conditional_edges")


class GraphState(TypedDict):
    question: str
    documents: List[str]
    generation: str
    retry_count: int
    web_search: str


def build_app():
    workflow = StateGraph(GraphState)

    # 노드 등록
    workflow.add_node("retrieve",        _nodes.retrieve)
    workflow.add_node("grade_documents", _nodes.grade_documents)
    workflow.add_node("generate",        _nodes.generate)
    workflow.add_node("transform_query", _nodes.transform_query)
    workflow.add_node("do_web_search",   _nodes.web_search)  # LangGraph 1.x: 노드명 ≠ State 필드명

    # 엣지 연결
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "grade_documents")

    workflow.add_conditional_edges(
        "grade_documents",
        _edges.decide_to_generate,
        {"transform_query": "transform_query", "generate": "generate"},
    )
    workflow.add_edge("transform_query", "do_web_search")
    workflow.add_edge("do_web_search", "grade_documents")   # 순환!

    workflow.add_conditional_edges(
        "generate",
        _edges.grade_generation,
        {
            "not_supported": "generate",     # 환각 → 재생성
            "useful":         END,           # 통과 → 종료
            "not_useful":     "transform_query",
        },
    )

    return workflow.compile()


def run_one(question: str) -> None:
    app = build_app()
    inputs = {"question": question, "retry_count": 0}

    print("\n" + "═" * 70)
    print(f"🚀 RUN: {question}")
    print("═" * 70)

    last_state = None
    for output in app.stream(inputs, {"recursion_limit": 25}):
        for node_name, payload in output.items():
            print(f"  ▶ [{node_name}] 완료")
            last_state = payload

    if last_state and "generation" in last_state:
        print("\n📝 최종 답변")
        print("-" * 70)
        print(last_state["generation"])
    else:
        print("\n(생성 단계 도달 못함)")


if __name__ == "__main__":
    # ── 데모 1: SAMPLE_DOCS 에 답이 있는 케이스 (벡터DB 경로만 사용) ──
    #    예상 트레이스: retrieve → grade(통과 ≥1) → generate → useful=yes → END
    run_one("에이전트 메모리에는 어떤 종류가 있나?")

    # ── 데모 2: SAMPLE_DOCS 에 답이 없는 케이스 (웹 폴백 경로) ──
    #    예상 트레이스: retrieve → grade(0/4) → transform_query → web_search →
    #                  grade(다시) → generate → END (혹은 재시도 후 종료)
    #    핵심 관찰 포인트:
    #      - decide_to_generate 가 "transform_query" 로 분기
    #      - web_search → grade_documents 의 *순환 (cycle)* 엣지가 발화
    #      - retry_count 가 MAX_RETRIES 에 도달하면 강제 종료되는 안전장치
    run_one("오늘 비트코인 가격은 얼마인가?")
