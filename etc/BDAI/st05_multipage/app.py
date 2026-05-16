"""
app.py — 멀티페이지 진입점
강의안 섹션 2-7 대응

실행:
    cd streamlit_practice/st05_multipage
    streamlit run app.py
"""
import streamlit as st

st.set_page_config(
    page_title="AI 프로젝트",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─ 공통 사이드바 (모든 페이지 공유) ─
from components.sidebar import render_common_sidebar

render_common_sidebar()

# ─ 홈 ─
st.title("🤖 AI 프로젝트 홈")
st.write(
    "왼쪽 사이드바에서 원하는 페이지를 선택하세요. "
    "이 앱은 `pages/` 디렉토리의 파일이 자동으로 메뉴에 등록됩니다."
)

st.divider()

c1, c2, c3 = st.columns(3)
with c1:
    st.subheader("💬 Chat")
    st.write("LLM 챗봇 인터페이스 — 스트리밍 + 시스템 프롬프트 지원")
with c2:
    st.subheader("📄 Documents")
    st.write("PDF/TXT/CSV 업로드 및 텍스트 추출")
with c3:
    st.subheader("📊 Dashboard")
    st.write("사용 통계 및 모니터링 대시보드")

st.divider()

st.subheader("📁 프로젝트 구조")
st.code(
    """
st05_multipage/
├── app.py                  # 진입점 (현재 파일)
├── pages/
│   ├── 1_💬_Chat.py
│   ├── 2_📄_Documents.py
│   └── 3_📊_Dashboard.py
├── components/
│   ├── sidebar.py          # 공통 사이드바
│   └── chat_ui.py          # 챗 UI 헬퍼
├── core/
│   └── llm.py              # LLM 클라이언트
└── .streamlit/
    ├── secrets.toml        # ⚠️ git ignore
    └── secrets.toml.example
""".strip(),
    language="text",
)
