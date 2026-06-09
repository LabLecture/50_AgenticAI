"""
13_customer_support_app.py — 종합: 코디네이터 + 조사 파이프라인 + HITL

지금까지 만든 모든 패턴 통합:
  - 코디네이터 (06) 가 의도 분류 + 위임
  - 조사 파이프라인 (04 SequentialAgent) 는 정보성 문의 처리
  - 환불 처리는 콜백 가드레일 (11) 로 HITL 안전망
  - 일반 응답은 load_memory (10) 로 과거 선호 참고

이 구조가 강의안 §5.1 의 종합 설계와 1:1 매핑.
"""
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import load_memory
from google.adk.tools.tool_context import ToolContext

from _adk_common import adk_model, banner


# ─── 조사 파이프라인 ───
searcher = LlmAgent(
    name="searcher", model=adk_model(),
    instruction="문의 키워드에 대해 핵심 정보 2 줄 정리.",
    output_key="research",
)
summarizer = LlmAgent(
    name="summarizer", model=adk_model(),
    instruction="다음 조사를 사용자에게 한 단락으로 정리:\n{research}",
    output_key="answer",
)
research_pipeline = SequentialAgent(
    name="research_pipeline",
    sub_agents=[searcher, summarizer],
    description="고객 문의에 대한 조사 → 정리 파이프라인",
)


# ─── 환불 처리 + HITL 가드레일 ───
def process_refund(amount: int, reason: str) -> dict:
    """환불을 실행한다.

    Args:
        amount: 환불 금액.
        reason: 환불 사유.
    """
    return {"status": "success", "message": f"{amount:,}원 환불 완료 ({reason})"}


def refund_guardrail(tool, args, tool_context: ToolContext):
    """고액 환불은 사람 확인 강제."""
    if tool.name == "process_refund" and args.get("amount", 0) >= 500_000:
        return {
            "status": "blocked",
            "message": (
                f"{args.get('amount'):,}원 환불은 50만원 이상이라 관리자 승인이 필요합니다. "
                f"사용자에게 절차를 안내하세요."
            ),
        }
    return None


refund_agent = LlmAgent(
    name="refund_agent",
    model=adk_model(),
    description="환불 신청을 처리한다.",
    instruction=(
        "환불 요청은 process_refund 호출. blocked 가 오면 그 메시지를 그대로 안내."
    ),
    tools=[process_refund],
    before_tool_callback=refund_guardrail,
)


# ─── 코디네이터 (root) ───
root_agent = LlmAgent(
    name="coordinator",
    model=adk_model(),
    description="고객 지원 멀티에이전트 라우터",
    instruction=(
        "사용자 문의를 분석해 분기하라:\n"
        "- 정보성 질문 (요금제·정책·이용 방법) → research_pipeline 위임\n"
        "- 환불 신청 → refund_agent 위임\n"
        "- 사용자 이력이 필요하면 load_memory 사용\n"
        "직접 답하지 말고 위임 결과를 사용자에게 전달."
    ),
    sub_agents=[research_pipeline, refund_agent],
    tools=[load_memory],
)


def main() -> None:
    banner("종합 — 고객지원 멀티에이전트 (코디네이터 + 파이프라인 + HITL + Memory)")
    print(f"\n  ✅ 구조 정의 완료. root_agent='coordinator'")
    print(f"     ├─ sub_agents:")
    print(f"     │    ├─ research_pipeline (SequentialAgent)")
    print(f"     │    │    ├─ searcher")
    print(f"     │    │    └─ summarizer")
    print(f"     │    └─ refund_agent (+ before_tool_callback=refund_guardrail)")
    print(f"     └─ tools=[load_memory]")
    print(f"\n  → 실제 실행은 'adk web .' 또는 'adk run .' 로 (브라우저 UI 가 코디네이터 분기/HITL 승인/Memory 회상을 시각화)")
    print(f"\n  💡 강의안 §5.1 의 종합 설계가 코드로 그대로 구현된 모습")


if __name__ == "__main__":
    main()
