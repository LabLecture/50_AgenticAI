"""
10_agent_with_memory.py — load_memory 도구로 과거 기억 능동 검색

에이전트가 *필요할 때* load_memory 를 호출해 과거 세션의 기억을 가져온다.
시나리오: 세션1 에서 음식 선호 적재 → 세션2 에서 load_memory 로 회상.

⚠ load_memory 의 검색 결과 포맷은 SDK 버전 의존. 본 데모는 *호출 형태만* 시연.
"""
import asyncio

from google.adk.agents import LlmAgent
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import load_memory
from google.genai.types import Content, Part

from _adk_common import adk_model, banner, adk_unavailable


async def demo() -> None:
    sess_svc = InMemorySessionService()
    mem_svc = InMemoryMemoryService()

    # ─── 세션 1: 사용자가 음식 선호 알려줌 ───
    s1 = await sess_svc.create_session(app_name="food_app", user_id="alice", session_id="d1")
    s1.state["favorite_food"] = "매운 떡볶이"
    await mem_svc.add_session_to_memory(s1)
    print(f"  📦 세션 1 완료 → 메모리 적재 (favorite_food='매운 떡볶이')")

    # ─── 세션 2: 새 에이전트가 load_memory 로 회상해 답변 ───
    agent = LlmAgent(
        name="memory_agent",
        model=adk_model(),
        instruction=(
            "사용자 선호를 알고 답변해야 한다. 모르면 load_memory 도구로 "
            "과거 대화를 검색해 참고하라. 한국어 한 문장."
        ),
        tools=[load_memory],
    )

    runner = Runner(
        agent=agent, app_name="food_app",
        session_service=sess_svc, memory_service=mem_svc,
    )
    await sess_svc.create_session(app_name="food_app", user_id="alice", session_id="d2")
    msg = Content(role="user", parts=[Part(text="내가 좋아하는 음식 스타일은?")])
    print(f"\n  ❓ d2 user : 내가 좋아하는 음식 스타일은?")
    final = ""
    async for event in runner.run_async(user_id="alice", session_id="d2", new_message=msg):
        if event.is_final_response() and event.content and event.content.parts:
            final = event.content.parts[0].text or ""
            break
    print(f"  💬 d2 bot  : {final[:200]}")


def main() -> None:
    banner("load_memory — 과거 세션 회상")
    try:
        asyncio.run(demo())
    except Exception as e:
        print(f"\n  ⚠ {type(e).__name__}: {str(e)[:200]}")
        adk_unavailable()


if __name__ == "__main__":
    main()
