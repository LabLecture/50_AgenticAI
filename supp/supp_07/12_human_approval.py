"""
12_human_approval.py — HITL #2: LongRunningFunctionTool (승인 대기)

진짜 "사람을 기다리는" HITL — 도구가 즉시 완료 안 하고 pending 상태로 일시 중단.
실제 운영은 ADK Web UI 가 사람의 응답을 받아 재개. 본 스크립트는 *정의/구조* 시연.
"""
from google.adk.agents import LlmAgent
from google.adk.tools import LongRunningFunctionTool
from google.adk.tools.tool_context import ToolContext

from _adk_common import adk_model, banner


def request_approval(action: str, amount: int, tool_context: ToolContext) -> dict:
    """고위험 작업에 대해 사람의 승인을 요청한다 (롱러닝).

    Args:
        action: 승인 요청할 작업 종류 (예: 'transfer_money').
        amount: 금액 등의 핵심 파라미터.
    Returns:
        status='pending' 으로 실행이 일시 중단되어 사람 응답 대기.
    """
    return {
        "status": "pending",
        "summary": f"[{action}] amount={amount:,} 의 승인을 관리자에게 요청했습니다.",
        "next": "관리자가 승인하면 자동 진행됩니다.",
    }


def main() -> None:
    banner("HITL #2 — LongRunningFunctionTool (승인 게이트)")

    approval_tool = LongRunningFunctionTool(func=request_approval)

    agent = LlmAgent(
        name="approval_agent",
        model=adk_model(),
        instruction=(
            "민감한 작업 (송금/삭제/외부 발송) 전에는 반드시 request_approval 도구를 "
            "먼저 호출. 도구가 'pending' 을 반환하면 그 summary 를 그대로 사용자에게 안내."
        ),
        tools=[approval_tool],
    )

    print(f"\n  ✅ LongRunningFunctionTool 등록 완료")
    print(f"     실행 흐름:")
    print(f"       1. Agent → request_approval 호출")
    print(f"       2. Runner 가 pending event yield → 실행 일시 중단")
    print(f"       3. ADK Web UI (또는 외부 시스템) 가 사람에게 표시")
    print(f"       4. 사람 응답 (승인/거부) → Runner 가 결과 주입해 재개")
    print(f"\n  → 본 모듈은 *구조 시연* 만 (UI 없이 자동 재개 트리거 부재).")
    print(f"     실 동작은 'adk web' 으로 띄워서 보면 pending event 가 UI 에 표시됨.")


if __name__ == "__main__":
    main()
