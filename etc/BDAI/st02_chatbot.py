"""
st02_chatbot.py — Streamlit 챗봇 (비스트리밍 / 스트리밍 / 멀티턴)
강의안 섹션 2-3 대응

OpenRouter API 키 설정 방법 (택1):
  1) .streamlit/secrets.toml 파일에 OPENROUTER_API_KEY = "sk-or-..."
  2) 환경변수 OPENROUTER_API_KEY 설정
  3) 좌측 사이드바에서 직접 입력 (이번 세션 한정)

실행:
    streamlit run streamlit_practice/st02_chatbot.py
"""
import os
import streamlit as st
from openai import OpenAI, OpenAIError

st.set_page_config(page_title="St02 Chatbot", page_icon="🤖", layout="centered")

# =============================================================================
# 0. API 키 로드 (secrets → env → 사이드바 입력 순)
# =============================================================================
def get_api_key() -> str | None:
    # secrets.toml 우선
    try:
        return st.secrets["OPENROUTER_API_KEY"]
    except (KeyError, FileNotFoundError):
        pass
    # 환경변수
    if key := os.getenv("OPENROUTER_API_KEY"):
        return key
    # 세션 스토리지
    return st.session_state.get("api_key_input")


with st.sidebar:
    st.header("🔑 API 설정")
    st.text_input(
        "OPENROUTER_API_KEY",
        type="password",
        key="api_key_input",
        help="secrets.toml 또는 환경변수에 설정하면 이 칸은 생략 가능합니다.",
    )
    st.divider()
    mode = st.radio(
        "응답 모드",
        ["1️⃣ 비스트리밍", "2️⃣ 스트리밍", "3️⃣ 멀티턴+시스템프롬프트"],
        index=1,
    )
    if st.button("🗑 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

api_key = get_api_key()

# =============================================================================
# 1. 클라이언트 (지연 생성)
# =============================================================================
def get_client() -> OpenAI | None:
    if not api_key:
        return None
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

MODEL = "anthropic/claude-3.5-sonnet"
SYSTEM_PROMPT = """당신은 친절한 AI 어시스턴트입니다.
사용자의 질문에 정확하고 간결하게 답변하세요.
한국어로 답변하세요."""

# =============================================================================
# 2. 메시지 히스토리 초기화
# =============================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🤖 AI 어시스턴트")
st.caption(f"모드: **{mode}** · 모델: `{MODEL}`")

if not api_key:
    st.warning(
        "🔑 OPENROUTER_API_KEY가 설정되지 않았습니다. "
        "사이드바에서 입력하거나 secrets.toml에 등록하세요."
    )

# =============================================================================
# 3. 이전 대화 렌더링
# =============================================================================
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue  # 시스템 프롬프트는 화면에 표시하지 않음
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# =============================================================================
# 4. 사용자 입력 처리
# =============================================================================
if prompt := st.chat_input("메시지를 입력하세요..."):
    if not api_key:
        st.error("API 키를 먼저 설정해 주세요.")
        st.stop()

    client = get_client()
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 모드별 메시지 구성
    if mode.startswith("3"):
        full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
            m for m in st.session_state.messages if m["role"] != "system"
        ]
    else:
        full_messages = st.session_state.messages

    with st.chat_message("assistant"):
        try:
            if mode.startswith("2"):
                # 스트리밍
                stream = client.chat.completions.create(
                    model=MODEL,
                    messages=full_messages,
                    stream=True,
                )
                answer = st.write_stream(stream)
            else:
                # 비스트리밍 (1, 3 모두 동일)
                with st.spinner("🤖 생각 중..."):
                    response = client.chat.completions.create(
                        model=MODEL,
                        messages=full_messages,
                        max_tokens=2048,
                        temperature=0.7,
                    )
                answer = response.choices[0].message.content
                st.markdown(answer)
        except OpenAIError as e:
            st.error(f"API 호출 실패: {e}")
            st.stop()

    st.session_state.messages.append({"role": "assistant", "content": answer})
