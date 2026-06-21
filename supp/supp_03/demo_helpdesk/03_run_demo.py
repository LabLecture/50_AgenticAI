"""
03_run_demo.py — 시나리오 A-1 데모 스토리 5턴을 그대로 재현 (헤드리스).

시연 흐름 (supp_03_04_종합실습_시나리오안.md):
  1. "연차가 며칠 남았어요?"            → db 라우팅 → 사번 슬롯필링 질문
  2. "E1003"                            → 슬롯 채움 → DB 조회 → 잔여 12일
  3. "연차 이월은 어떻게 되나요?"        → doc 라우팅 → 취업규칙 §12 인용
  4. "작년에 이월한 연차도 올해 쓸 수 있어요?" → hybrid → 규정 + 내 이월 3일 종합
  5. "주4일제는 언제 도입되나요?"        → grade 불합격 → rewrite ×2 → 정직한 "근거 없음"
"""
import importlib

_graph_mod = importlib.import_module("02_graph")
build_graph, run_turn = _graph_mod.build_graph, _graph_mod.run_turn
from _demo_common import banner  # noqa: E402

TURNS = [
    "연차가 며칠 남았어요?",
    "E1003 이요",
    "연차 이월은 어떻게 되나요?",
    "작년에 이월한 연차도 올해 쓸 수 있어요?",
    "주4일제는 언제 도입되나요?",
]


def main() -> None:
    banner("사내 헬프데스크 에이전트 — 5턴 데모")
    graph = build_graph()
    thread = "demo-001"

    for i, text in enumerate(TURNS, 1):
        print(f"\n{'─' * 70}")
        print(f"👤 [{i}] {text}")
        result = run_turn(graph, thread, text)
        for step in result.get("trace", []):
            print(f"   ⚙ {step}")
        print(f"🤖 {result['answer']}")

    print(f"\n{'═' * 70}")
    print("데모 종료 — 슬롯필링·라우팅·CRAG 분기가 모두 시연되었다.")


if __name__ == "__main__":
    main()
