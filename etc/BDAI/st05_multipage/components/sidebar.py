"""공통 사이드바 컴포넌트 — 모든 페이지에서 import 해서 사용."""
import streamlit as st


MODELS = [
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "meta-llama/llama-3.1-70b-instruct",
    "google/gemini-flash-1.5",
]

DEFAULT_SYSTEM_PROMPT = "당신은 친절한 AI 어시스턴트입니다."


def init_session_defaults() -> None:
    """앱 전체에서 공유하는 session_state 기본값."""
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("uploaded_context", "")
    st.session_state.setdefault("selected_model", MODELS[0])
    st.session_state.setdefault("temperature", 0.7)
    st.session_state.setdefault("max_tokens", 2048)
    st.session_state.setdefault("system_prompt", DEFAULT_SYSTEM_PROMPT)


def render_common_sidebar() -> None:
    """모든 페이지에 공통으로 노출되는 사이드바 위젯."""
    init_session_defaults()
    with st.sidebar:
        st.header("⚙️ 공통 설정")

        st.selectbox(
            "LLM 모델", MODELS,
            index=MODELS.index(st.session_state.selected_model),
            key="selected_model",
        )
        st.slider("Temperature", 0.0, 1.0, key="temperature", step=0.05)
        st.number_input("Max Tokens", 256, 8192, step=256, key="max_tokens")

        with st.expander("🔑 API Key (세션 한정)"):
            st.text_input(
                "OPENROUTER_API_KEY",
                type="password",
                key="api_key_input",
                help="secrets.toml 또는 환경변수에 설정하면 생략 가능",
            )

        with st.expander("🧠 시스템 프롬프트"):
            st.text_area(
                "system prompt",
                key="system_prompt",
                height=120,
            )

        st.divider()
        st.caption(
            f"💬 대화 {len(st.session_state.messages)}건 · "
            f"📄 컨텍스트 {len(st.session_state.uploaded_context):,}자"
        )
