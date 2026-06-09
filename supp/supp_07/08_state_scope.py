"""
08_state_scope.py — State 의 4 가지 스코프 접두사

(없음)     : 현재 세션만
user:      : 같은 사용자의 모든 세션 공유
app:       : 앱 전체 공유
temp:      : 현재 턴만 (영속 X)

⚠ ADK 의 InMemorySessionService 는 user:/app: 도 *해당 svc 인스턴스 내* 에서만 공유.
   실제 영속/공유는 DatabaseSessionService 또는 VertexAiSessionService 가 필요.
"""
import asyncio

from google.adk.sessions import InMemorySessionService

from _adk_common import banner


async def demo() -> None:
    svc = InMemorySessionService()

    # 세션 A 에서 다양한 스코프 키 작성
    a = await svc.create_session(app_name="app", user_id="alice", session_id="A")
    a.state["topic"] = "오늘 주제"               # 세션 한정
    a.state["user:lang"] = "ko"                  # 사용자 공유
    a.state["app:version"] = "1.0"               # 앱 공유
    a.state["temp:scratch"] = "1회용"             # 임시
    print(f"  세션 A (alice/A) state:")
    for k, v in a.state.items():
        print(f"    {k:<22}= {v!r}")

    # 같은 사용자의 다른 세션 B — user: / app: 이 이어져야 함
    b = await svc.create_session(app_name="app", user_id="alice", session_id="B")
    print(f"\n  세션 B (alice/B) state:")
    for k, v in b.state.items():
        print(f"    {k:<22}= {v!r}")
    print(f"  → ADK InMemorySessionService 는 자동 스코프 전파를 *백엔드 구현 의존*")
    print(f"     운영 DatabaseSessionService 에서 user:/app: 가 실제로 공유됨.")

    print(f"\n  💡 스코프 선택 기준 (강의용)")
    print(f"     - 사용자 음식 선호 → user:favorite_food     (다음 세션도 기억)")
    print(f"     - 앱 글로벌 feature flag → app:dark_mode    (모든 사용자)")
    print(f"     - 이번 turn 의 LLM raw output → temp:raw    (안 남김)")
    print(f"     - 현재 대화의 의도 분류 결과 → intent       (이 세션만)")


def main() -> None:
    banner("State 스코프 — (없음) / user: / app: / temp:")
    asyncio.run(demo())


if __name__ == "__main__":
    main()
