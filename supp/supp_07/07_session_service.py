"""
07_session_service.py — SessionService 생애주기 (InMemory)

세션은 *하나의 대화 스레드*. 이벤트 이력 + State 보유.
InMemory / Database / VertexAi 구현이 같은 인터페이스 — 운영은 DB/Vertex 로 교체만.
"""
import asyncio

from google.adk.sessions import InMemorySessionService

from _adk_common import banner


async def demo() -> None:
    svc = InMemorySessionService()

    # 1) 생성
    session = await svc.create_session(
        app_name="my_app", user_id="user1", session_id="sess1"
    )
    print(f"  ✅ 생성: id={session.id}, app={session.app_name}, user={session.user_id}")

    # 2) state 직접 갱신
    session.state["intent"] = "greeting"
    session.state["user:lang"] = "ko"   # 사용자 스코프
    print(f"  📝 state: {dict(session.state)}")

    # 3) 조회 (기존 대화 이어가기)
    same = await svc.get_session(
        app_name="my_app", user_id="user1", session_id="sess1"
    )
    print(f"  🔄 재조회: state={dict(same.state)}  ← 같은 객체 그대로")

    # 4) 다른 세션 생성 — state 가 *분리* 됨
    other = await svc.create_session(
        app_name="my_app", user_id="user1", session_id="sess2"
    )
    print(f"\n  🆕 다른 세션 (sess2): state={dict(other.state)}  ← 깨끗")
    print(f"  💡 user: 접두사가 붙은 키는 *같은 사용자의 다른 세션* 으로 공유 가능 (08 참조)")


def main() -> None:
    banner("SessionService — 생성 / 갱신 / 조회 / 격리")
    asyncio.run(demo())


if __name__ == "__main__":
    main()
