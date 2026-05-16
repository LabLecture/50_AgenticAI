"""
st03_sidebar.py — 사이드바 설정 패널 + 챗봇 통합
강의안 섹션 2-4 대응

기능:
  • 모델 선택 (selectbox)
  • Temperature / Max Tokens 조정
  • 시스템 프롬프트 커스터마이징 (expander)
  • 대화 초기화 / JSON 내보내기

실행:
    streamlit run streamlit_practice/st03_sidebar.py
"""
import json
import os
import streamlit as st
from openai import OpenAI, OpenAIError

st.set_page_config(page_title="St03 Sidebar", page_icon="⚙️", layout="centered")

# =============================================================================
# 0. session_state 기본값
# =============================================================================
DEFAULT_SYSTEM_PROMPT = "당신은 친절한 AI 어시스턴트입니다."

if "messages" not in st.session_state:
    st.session_state.messages = []
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = DEFAULT_SYSTEM_PROMPT

# =============================================================================
# 1. API 키 로드 헬퍼
# =============================================================================
def get_api_key() -> str | None:
    try:
        return st.secrets["OPENROUTER_API_KEY"]
    except (KeyError, FileNotFoundError):
        pass
    if key := os.getenv("OPENROUTER_API_KEY"):
        return key
    return st.session_state.get("api_key_input")

# =============================================================================
# 2. 사이드바
# =============================================================================
with st.sidebar:
    st.header("⚙️ 설정")

    # ─ 모델 선택 ─────────────────────────────
    st.selectbox(
        "LLM 모델",
        [
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "meta-llama/llama-3.1-70b-instruct",
            "google/gemini-flash-1.5",
        ],
        index=0,
        key="selected_model",
    )

    # ─ 생성 파라미터 ─────────────────────────
    st.slider("Temperature", 0.0, 1.0, 0.7, step=0.05, key="temperature")
    st.number_input("Max Tokens", 256, 8192, 2048, step=256, key="max_tokens")

    st.divider()

    # ─ API 키 ─────────────────────────────
    with st.expander("🔑 API Key"):
        st.text_input(
            "OPENROUTER_API_KEY",
            type="password",
            key="api_key_input",
            help="secrets.toml 또는 환경변수에 설정하면 생략 가능",
        )

    # ─ 시스템 프롬프트 ─────────────────────
    # key= 만 사용하면 session_state와 자동 양방향 바인딩되며, value= 와 함께 쓰면 경고가 뜬다.
    with st.expander("🧠 시스템 프롬프트 편집"):
        st.text_area(
            "시스템 프롬프트",
            height=120,
            key="system_prompt",
        )

    st.divider()

    # ─ 대화 관리 ─────────────────────────
    st.subheader("💬 대화 관리")
    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button("🗑 초기화", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with bc2:
        if st.session_state.messages:
            history_json = json.dumps(
                st.session_state.messages, ensure_ascii=False, indent=2
            )
            st.download_button(
                "💾 저장",
                data=history_json,
                file_name="chat_history.json",
                mime="application/json",
                use_container_width=True,
            )
        else:
            st.button("💾 저장", disabled=True, use_container_width=True)

    st.divider()
    st.caption(f"총 대화 수: **{len(st.session_state.messages)}**")

# =============================================================================
# 3. 본문 — 챗봇
# =============================================================================
st.title("⚙️ 사이드바 설정 챗봇")
st.caption(
    f"모델 `{st.session_state.selected_model}` · "
    f"T={st.session_state.temperature} · max_tokens={st.session_state.max_tokens}"
)

api_key = get_api_key()
if not api_key:
    st.warning("🔑 API 키가 없습니다. 사이드바의 'API Key' 섹션에서 입력하세요.")

# 이전 대화 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 사용자 입력
if prompt := st.chat_input("메시지를 입력하세요..."):
    if not api_key:
        st.error("API 키를 먼저 설정해 주세요.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    full_messages = (
        [{"role": "system", "content": st.session_state.system_prompt}]
        + st.session_state.messages
    )

    with st.chat_message("assistant"):
        try:
            stream = client.chat.completions.create(
                model=st.session_state.selected_model,
                messages=full_messages,
                temperature=st.session_state.temperature,
                max_tokens=st.session_state.max_tokens,
                stream=True,
            )
            answer = st.write_stream(stream)
        except OpenAIError as e:
            st.error(f"API 호출 실패: {e}")
            st.stop()

    st.session_state.messages.append({"role": "assistant", "content": answer})
