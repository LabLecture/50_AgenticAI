"""
09_memory_service.py — MemoryService: 세션을 넘는 장기 기억

Session/State = "이번 대화", Memory = "지난 대화들의 아카이브".
완료된 세션을 add_session_to_memory 로 적재 → 다음 세션에서 검색 (10_agent_with_memory.py)
"""
import asyncio

from google.adk.memory import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService

from _adk_common import banner


async def demo() -> None:
    sess_svc = InMemorySessionService()
    mem_svc = InMemoryMemoryService()

    # 1) 첫 세션에서 사용자 선호 정보 누적
    s1 = await sess_svc.create_session(app_name="app", user_id="alice", session_id="day1")
    s1.state["favorite_food"] = "매운 떡볶이"
    s1.state["allergy"] = "없음"
    print(f"  세션 day1 종료 시 state: {dict(s1.state)}")

    # 2) 완료된 세션을 장기 기억에 적재
    await mem_svc.add_session_to_memory(s1)
    print(f"\n  📦 add_session_to_memory(day1) — 장기 기억에 보관됨")

    # 3) 새 세션에서 메모리 검색
    s2 = await sess_svc.create_session(app_name="app", user_id="alice", session_id="day2")
    print(f"\n  새 세션 day2 (state 비어있음): {dict(s2.state)}")
    print(f"\n  🔍 search_memory('음식 취향') →")
    try:
        result = await mem_svc.search_memory(
            app_name="app", user_id="alice", query="음식 취향"
        )
        for mem in result.memories[:3]:
            print(f"    - {mem}")
    except Exception as e:
        # InMemoryMemoryService 의 search API 는 SDK 버전마다 시그니처가 다름
        print(f"    (search_memory API 시그니처는 SDK 버전 의존: {type(e).__name__})")

    print(f"\n  💡 실무 의미")
    print(f"     - 사용자가 1주일 뒤에 다시 와도 '매운 떡볶이 좋아함' 회상 가능")
    print(f"     - InMemoryMemoryService 는 데모용 (재시작 시 소실)")
    print(f"     - 운영 → VertexAiMemoryBankService (의미 검색 / 영속 보관)")
    print(f"     - ⚠ 프라이버시: 동의 / 보존기간 / 삭제 정책 필수")


def main() -> None:
    banner("MemoryService — 세션 → 장기 기억 적재")
    asyncio.run(demo())


if __name__ == "__main__":
    main()
