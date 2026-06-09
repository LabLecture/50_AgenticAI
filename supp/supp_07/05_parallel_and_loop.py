"""
05_parallel_and_loop.py — ParallelAgent / LoopAgent 패턴 시연

ParallelAgent: 두 에이전트 동시 실행 (서로 다른 output_key 필수)
LoopAgent:     비평 → 개선을 만족할 때까지 반복. escalate 또는 max_iterations 로 종료.

⚠ 본 실습은 LLM 호출이 많아 free 모델 429 위험. 가벼운 구성만 시연.
"""
from google.adk.agents import LlmAgent, ParallelAgent, LoopAgent
from google.adk.tools.tool_context import ToolContext

from _adk_common import adk_model, run_once, banner, adk_unavailable


def exit_loop(tool_context: ToolContext):
    """비평 결과 더 고칠 게 없을 때 호출해 루프를 종료한다."""
    tool_context.actions.escalate = True
    return {"status": "exit"}


def main() -> None:
    banner("Parallel / Loop Workflow Agents — 골격 시연")

    # === ParallelAgent ===
    src_a = LlmAgent(
        name="src_a", model=adk_model(),
        instruction="주제에 대해 *학술적* 관점 한 문장만 출력. 다른 말 금지.",
        output_key="academic",
    )
    src_b = LlmAgent(
        name="src_b", model=adk_model(),
        instruction="주제에 대해 *실무적* 관점 한 문장만 출력. 다른 말 금지.",
        output_key="industry",      # 다른 키!
    )
    gather = ParallelAgent(name="gather", sub_agents=[src_a, src_b])

    # === LoopAgent (개념 정의만 — 실제 LLM 호출은 위 Parallel 만 시연) ===
    refiner = LlmAgent(
        name="refiner", model=adk_model(),
        instruction="초안 {draft} 를 한 줄 더 다듬어라.",
        output_key="draft",
    )
    critic = LlmAgent(
        name="critic", model=adk_model(),
        instruction=(
            "초안 {draft} 를 한 줄로 평가. 문제 없으면 exit_loop 호출."
        ),
        tools=[exit_loop],
    )
    refine_loop = LoopAgent(
        name="refine_loop",
        sub_agents=[refiner, critic],
        max_iterations=3,
    )

    print(f"\n  ✅ ParallelAgent 'gather' — sub_agents 2 개가 동시 실행")
    print(f"     각자 다른 output_key (academic / industry) 로 state 충돌 회피")
    print(f"\n  ✅ LoopAgent 'refine_loop' — max_iterations=3, escalate 종료")
    print(f"     critic 이 만족하면 exit_loop 도구로 escalate=True 신호")

    # 실제 실행 — Parallel 만 (LoopAgent 는 호출량이 커서 정의만 보여줌)
    print(f"\n  ▶ Parallel 실제 실행: '도구 호출 (function calling)' 주제")
    try:
        result = run_once(gather, "도구 호출 (function calling)")
        print(f"  💬 최종 응답 (병렬 에이전트는 final 답변 없을 수 있음):")
        print(f"     {result[:200]}")
        print(f"\n  → 두 sub_agent 가 state['academic'], state['industry'] 에 *동시* 기록")
    except Exception as e:
        print(f"  ⚠ {type(e).__name__}: {str(e)[:150]}")
        adk_unavailable()


if __name__ == "__main__":
    main()
