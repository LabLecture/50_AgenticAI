"""
06_coordinator.py — 동적 라우팅: LLM 이 sub_agent 에 위임

워크플로우 에이전트가 *고정 순서* 라면, LlmAgent 에 sub_agents 를 붙이면
*LLM 이 판단해서* 적절한 하위 에이전트로 위임. supervisor/dispatcher 패턴.
"""
from google.adk.agents import LlmAgent

from _adk_common import adk_model, run_once, banner, adk_unavailable


def main() -> None:
    banner("Coordinator — LLM 기반 동적 위임 (transfer)")

    billing = LlmAgent(
        name="billing",
        model=adk_model(),
        description="결제·환불 문의를 처리한다.",
        instruction=(
            "너는 결제팀 담당이다. 결제 / 환불 / 청구 관련 문의에만 답하라. "
            "한국어 한 문장."
        ),
    )

    support = LlmAgent(
        name="support",
        model=adk_model(),
        description="기술 지원 문의를 처리한다.",
        instruction=(
            "너는 기술지원팀 담당이다. 제품 사용법 / 에러 / 버그 문의에만 답하라. "
            "한국어 한 문장."
        ),
    )

    coordinator = LlmAgent(
        name="coordinator",
        model=adk_model(),
        description="고객 문의 라우터",
        instruction=(
            "사용자 문의를 분석해서 결제 관련이면 billing, 기술 문의면 support "
            "에게 transfer 하라. 직접 답하지 말고 반드시 위임하라."
        ),
        sub_agents=[billing, support],
    )

    cases = [
        "환불 신청 방법 알려줘",
        "앱이 자꾸 강제종료돼요",
    ]
    for q in cases:
        print(f"\n  ❓ {q}")
        try:
            reply = run_once(coordinator, q)
            print(f"  💬 {reply[:200]}")
        except Exception as e:
            print(f"  ⚠ {type(e).__name__}: {str(e)[:120]}")
            adk_unavailable()
            break


if __name__ == "__main__":
    main()
