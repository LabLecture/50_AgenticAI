"""
02_agent_with_tools.py — 함수를 도구로 등록한 에이전트

ADK 는 파이썬 함수를 그대로 도구로 받는다. *docstring + 타입 힌트* 가 LLM 의
도구 이해를 결정 — 명확히 작성해야 LLM 이 도구를 올바르게 호출한다.
"""
from google.adk.agents import LlmAgent

from _adk_common import adk_model, banner


def get_weather(city: str) -> dict:
    """지정한 도시의 현재 날씨를 반환한다.

    Args:
        city: 날씨를 조회할 도시 이름 (예: "Seoul", "Busan").
    Returns:
        status 와 report 를 담은 dict. 없는 도시면 error.
    """
    data = {"Seoul": "맑음, 22도", "Busan": "흐림, 24도"}
    if city in data:
        return {"status": "success", "report": data[city]}
    return {"status": "error", "message": f"{city}의 날씨 정보가 없습니다."}


def main() -> None:
    banner("ADK — 도구를 가진 에이전트")

    agent = LlmAgent(
        name="weather_agent",
        model=adk_model(),
        description="도시 날씨를 알려주는 에이전트",
        instruction="사용자가 날씨를 물으면 get_weather 도구를 사용해 답하라.",
        tools=[get_weather],
    )

    print(f"\n  ✅ tools=[get_weather] 등록")
    print(f"     docstring/typing 이 LLM 에 그대로 전달 → 도구 호출 정확도 결정")
    print(f"\n  → 실행은 03_run_with_runner.py 에서 weather_agent 로 교체해 시연")


if __name__ == "__main__":
    main()
