"""
11_callback_guardrail.py — HITL #1: 콜백 가드레일 (동기 차단)

before_tool_callback 으로 *고위험* 인자를 검사. 위험하면 도구를 우회하고
대체 응답을 반환 → 사람 확인 유도.
"""
from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext

from _adk_common import adk_model, run_once, banner, adk_unavailable


def transfer_money(amount: int, to: str) -> dict:
    """지정 금액을 송금한다 (고위험 행동).

    Args:
        amount: 송금 금액 (원).
        to: 수취인.
    """
    return {"status": "success",
            "message": f"{to} 에게 {amount:,}원 송금 완료"}


def before_tool(tool, args, tool_context: ToolContext):
    """고액 송금은 자동 실행을 막고 사람 확인을 유도한다."""
    if tool.name == "transfer_money":
        amount = args.get("amount", 0)
        if amount >= 1_000_000:
            # None 이 아닌 dict 를 반환하면 *실제 도구 호출을 건너뛰고* 이 결과를 사용
            return {
                "status": "blocked",
                "message": (
                    f"{amount:,}원 송금은 100만원 이상이라 관리자 승인이 필요합니다. "
                    f"사용자에게 안내하세요."
                ),
            }
    return None  # None → 정상 도구 호출 진행


def main() -> None:
    banner("HITL #1 — before_tool_callback 가드레일")

    agent = LlmAgent(
        name="payment_agent",
        model=adk_model(),
        instruction=(
            "사용자가 송금을 요청하면 transfer_money 도구를 사용. "
            "도구가 blocked 를 반환하면 그 메시지를 그대로 사용자에게 안내."
        ),
        tools=[transfer_money],
        before_tool_callback=before_tool,
    )

    cases = [
        ("정상 금액", "이수에게 5만원 송금해줘"),
        ("고액 차단", "이수에게 200만원 송금해줘"),
    ]
    for label, q in cases:
        print(f"\n  [{label}]  user: {q}")
        try:
            reply = run_once(agent, q)
            print(f"  💬 bot: {reply[:200]}")
        except Exception as e:
            print(f"  ⚠ {type(e).__name__}: {str(e)[:120]}")
            adk_unavailable()
            break


if __name__ == "__main__":
    main()
