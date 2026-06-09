"""
_adk_common.py — supp_07 공통 헬퍼

(1) OpenRouter free 모델을 LiteLlm 으로 wrap → ADK 의 LlmAgent 에 주입
(2) Runner 실행을 동기 함수 1 개로 단순화
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import asyncio
import os

# _common 의 .env 자동 로드 트리거
from _common import banner  # noqa
from _common import llm_unavailable as _shared_unavail


def adk_model(force: str | None = None):
    """ADK LlmAgent 의 model= 에 그대로 넣을 수 있는 LiteLlm 객체.

    OpenRouter free 모델 (.env 의 OPENROUTER_API_KEY) 을 사용.
    기본: google/gemma-4-26b-a4b-it:free (reasoning prefix 없는 일반 모델)
    `OPENROUTER_TEXT_MODEL` env 또는 force 인자로 덮어쓰기.
    """
    from google.adk.models.lite_llm import LiteLlm
    if force:
        return LiteLlm(model=f"openrouter/{force}")
    model = os.getenv("OPENROUTER_TEXT_MODEL", "google/gemma-4-26b-a4b-it:free")
    return LiteLlm(model=f"openrouter/{model}")


def run_once(agent, text: str, app_name: str = "demo_app",
             user_id: str = "u1", session_id: str = "s1") -> str:
    """가장 단순한 ADK Runner 실행 — 텍스트 보내고 최종 응답 1 개 받기.

    멀티턴/이벤트 스트림이 필요하면 직접 Runner.run_async 사용.
    """
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai.types import Content, Part

    sess = InMemorySessionService()
    runner = Runner(agent=agent, app_name=app_name, session_service=sess)

    async def _go() -> str:
        await sess.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
        msg = Content(role="user", parts=[Part(text=text)])
        final = ""
        async for event in runner.run_async(
            user_id=user_id, session_id=session_id, new_message=msg
        ):
            if event.is_final_response() and event.content and event.content.parts:
                final = event.content.parts[0].text or ""
                break
        return final

    return asyncio.run(_go())


def adk_unavailable() -> None:
    """ADK 의존성 / 키 미설정 시 안내."""
    if not os.getenv("OPENROUTER_API_KEY"):
        _shared_unavail()
        return
    print("⚠️ ADK 실행 실패 — google-adk[extensions] 설치 + OPENROUTER_API_KEY 확인.")
