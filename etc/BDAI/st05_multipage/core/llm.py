"""LLM 클라이언트 초기화 — secrets/env/세션 입력 순으로 키 탐색."""
import os
import streamlit as st
from openai import OpenAI


def get_api_key() -> str | None:
    try:
        return st.secrets["OPENROUTER_API_KEY"]
    except (KeyError, FileNotFoundError):
        pass
    if key := os.getenv("OPENROUTER_API_KEY"):
        return key
    return st.session_state.get("api_key_input")


def get_client() -> OpenAI | None:
    api_key = get_api_key()
    if not api_key:
        return None
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def build_messages(user_input: str) -> list[dict]:
    """시스템 프롬프트 + 업로드 컨텍스트 + 기존 히스토리 + 새 입력."""
    msgs: list[dict] = []
    msgs.append({"role": "system", "content": st.session_state.system_prompt})

    if ctx := st.session_state.uploaded_context:
        msgs.append({
            "role": "system",
            "content": f"다음 문서 내용을 참고하여 답변하세요:\n\n{ctx[:4000]}",
        })

    msgs.extend(st.session_state.messages)
    msgs.append({"role": "user", "content": user_input})
    return msgs
