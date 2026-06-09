"""
03_run_with_runner.py — Runner + SessionService 로 에이전트 실행

ADK 의 실행 모델: Runner 가 사용자 입력을 받아 에이전트를 호출하고
이벤트를 yield. Session 이 대화 상태를 저장.
"""
from google.adk.agents import LlmAgent
from importlib import import_module

from _adk_common import adk_model, run_once, banner, adk_unavailable

# 02 의 get_weather 함수 재사용
m02 = import_module("02_agent_with_tools")
get_weather = m02.get_weather


def main() -> None:
    banner("Runner + Session — 첫 실제 응답")

    agent = LlmAgent(
        name="weather_agent",
        model=adk_model(),
        description="도시 날씨를 알려주는 에이전트",
        instruction=(
            "사용자가 날씨를 물으면 get_weather 도구를 호출해 답하라. "
            "응답은 한국어 한 문장으로."
        ),
        tools=[get_weather],
    )

    try:
        reply = run_once(agent, "서울 날씨 어때?")
        print(f"\n  ❓ user : 서울 날씨 어때?")
        print(f"  💬 bot  : {reply[:200]}")
    except Exception as e:
        print(f"\n  ⚠ {type(e).__name__}: {str(e)[:200]}")
        adk_unavailable()


if __name__ == "__main__":
    main()
