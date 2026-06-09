"""
01_first_agent.py — 가장 단순한 LlmAgent

ADK 의 진입점은 LlmAgent. 4 필드 (name / model / description / instruction) 가 핵심.
"""
from google.adk.agents import LlmAgent

from _adk_common import adk_model, banner


def main() -> None:
    banner("ADK — 첫 LlmAgent (필드 4개만)")

    agent = LlmAgent(
        name="greeter",
        model=adk_model(),                            # OpenRouter free 모델
        description="사용자를 맞이하는 에이전트",
        instruction="너는 친절한 안내자다. 사용자의 인사에 한 줄로 답하라.",
    )

    print(f"\n  ✅ 에이전트 정의 완료")
    print(f"     name        = {agent.name}")
    print(f"     description = {agent.description}")
    print(f"     instruction = {agent.instruction[:50]}…")
    print(f"\n  → 실행은 03_run_with_runner.py 에서. 이 파일은 *정의* 만.")


if __name__ == "__main__":
    main()
