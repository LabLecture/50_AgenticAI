"""Dashboard 페이지 — 사용 통계 미니 대시보드."""
import streamlit as st
import pandas as pd

from components.sidebar import render_common_sidebar

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
render_common_sidebar()

st.title("📊 Dashboard")
st.caption("현재 세션의 사용 통계를 표시합니다.")

messages = st.session_state.messages

# ─ 메트릭 ─
m1, m2, m3, m4 = st.columns(4)
m1.metric("총 대화 수", len(messages))
m2.metric("사용자 메시지", sum(1 for m in messages if m["role"] == "user"))
m3.metric("어시스턴트 응답", sum(1 for m in messages if m["role"] == "assistant"))
m4.metric("컨텍스트 길이", f"{len(st.session_state.uploaded_context):,}자")

st.divider()

# ─ 메시지 길이 분포 ─
if messages:
    st.subheader("💬 메시지 길이 분포")
    df = pd.DataFrame([
        {"idx": i, "role": m["role"], "length": len(m["content"])}
        for i, m in enumerate(messages)
    ])
    st.bar_chart(df, x="idx", y="length", color="role")

    st.subheader("🗂 메시지 테이블")
    st.dataframe(
        df.assign(preview=[m["content"][:80] for m in messages]),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("아직 대화 기록이 없습니다. **Chat** 페이지에서 대화를 시작하세요.")

st.divider()

# ─ 현재 설정 요약 ─
st.subheader("⚙️ 현재 설정")
st.json({
    "selected_model": st.session_state.selected_model,
    "temperature": st.session_state.temperature,
    "max_tokens": st.session_state.max_tokens,
    "system_prompt_preview": st.session_state.system_prompt[:120],
})
