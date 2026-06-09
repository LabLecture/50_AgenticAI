"""
04_sequential_agent.py — SequentialAgent: 순차 워크플로우

핵심: `output_key` 로 한 에이전트의 출력을 State 에 저장하고,
다음 에이전트가 `instruction` 의 {키} 로 그 값을 참조.
"""
from google.adk.agents import LlmAgent, SequentialAgent

from _adk_common import adk_model, run_once, banner, adk_unavailable


def main() -> None:
    banner("SequentialAgent — 조사 → 작성 파이프라인")

    researcher = LlmAgent(
        name="researcher",
        model=adk_model(),
        instruction=(
            "다음 주제에 대해 핵심 사실 2 가지를 한 줄씩 정리하라. "
            "주제를 그대로 반복하지 말고 사실만 출력."
        ),
        output_key="research",        # 출력 → state["research"]
    )

    writer = LlmAgent(
        name="writer",
        model=adk_model(),
        instruction=(
            "다음 조사 결과를 바탕으로 한국어로 짧은 한 단락을 작성하라:\n\n"
            "조사 결과:\n{research}"   # state["research"] 참조
        ),
        output_key="article",
    )

    pipeline = SequentialAgent(
        name="research_pipeline",
        sub_agents=[researcher, writer],
        description="조사 후 글을 작성하는 순차 파이프라인",
    )

    try:
        reply = run_once(pipeline, "LangGraph 의 핵심 특징")
        print(f"\n  ❓ topic : LangGraph 의 핵심 특징")
        print(f"\n  💬 article (writer 출력)")
        print(f"  {reply[:400]}")
        print(f"\n  💡 출력은 state['article'] 에 저장됨 — 더 긴 파이프라인 가능")
    except Exception as e:
        print(f"\n  ⚠ {type(e).__name__}: {str(e)[:200]}")
        adk_unavailable()


if __name__ == "__main__":
    main()
