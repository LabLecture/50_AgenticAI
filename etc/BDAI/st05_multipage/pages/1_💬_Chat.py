"""Chat 페이지 — 스트리밍 챗봇."""
import streamlit as st
from openai import OpenAIError

from components.sidebar import render_common_sidebar
from core.llm import get_client, build_messages, get_api_key

st.set_page_config(page_title="Chat", page_icon="💬", layout="centered")
render_common_sidebar()

st.title("💬 Chat")
st.caption(
    f"`{st.session_state.selected_model}` · "
    f"T={st.session_state.temperature} · max_tokens={st.session_state.max_tokens}"
)

if not get_api_key():
    st.warning("🔑 사이드바에서 API Key를 설정하세요.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("메시지를 입력하세요..."):
    client = get_client()
    if client is None:
        st.error("API 키가 필요합니다.")
        st.stop()

    # 1) API 호출용 메시지는 session_state 갱신 전에 빌드 (user 중복 방지)
    msgs_for_api = build_messages(prompt)

    # 2) 화면용 히스토리 갱신
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            stream = client.chat.completions.create(
                model=st.session_state.selected_model,
                messages=msgs_for_api,
                temperature=st.session_state.temperature,
                max_tokens=st.session_state.max_tokens,
                stream=True,
            )
            answer = st.write_stream(stream)
        except OpenAIError as e:
            st.error(f"API 호출 실패: {e}")
            st.stop()

    st.session_state.messages.append({"role": "assistant", "content": answer})
