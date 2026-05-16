"""
st01_basics.py — Streamlit 기초 + UI 컴포넌트 종합 데모
강의안 섹션 2-1, 2-2 대응

실행:
    streamlit run streamlit_practice/st01_basics.py
"""
import streamlit as st

st.set_page_config(page_title="St01 Basics", page_icon="🧱", layout="wide")

# =============================================================================
# 0. session_state 초기화 (반드시 조건 체크)
# =============================================================================
if "count" not in st.session_state:
    st.session_state.count = 0
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "anthropic/claude-3.5-sonnet"

# =============================================================================
# 1. 텍스트 & 알림 컴포넌트
# =============================================================================
st.title("🧱 Streamlit 기초 컴포넌트 데모")
st.header("1. 텍스트 & 알림")
st.subheader("타이틀/헤더/서브헤더")
st.caption("st.caption — 보조 설명용 작은 글씨")

st.write("**st.write** — Markdown / 객체 자동 렌더링")
st.markdown("**굵게**, _기울임_, `인라인코드`, [Streamlit](https://streamlit.io)")
st.code("print('Hello, Streamlit!')", language="python")

c1, c2, c3, c4 = st.columns(4)
with c1: st.info("ℹ️ info")
with c2: st.warning("⚠️ warning")
with c3: st.error("❌ error")
with c4: st.success("✅ success")

st.divider()

# =============================================================================
# 2. 레이아웃 — 컬럼 & 탭
# =============================================================================
st.header("2. 레이아웃 — 컬럼 & 탭")

st.subheader("2-1. 균등 컬럼 + st.metric")
mc1, mc2, mc3 = st.columns(3)
with mc1:
    st.metric("총 문서 수", "1,234", delta="+56")
with mc2:
    st.metric("평균 응답 시간", "1.8s", delta="-0.3s", delta_color="inverse")
with mc3:
    st.metric("활성 사용자", "87", delta="+12")

st.subheader("2-2. 비율 지정 컬럼 (3:1)")
col_main, col_side = st.columns([3, 1])
with col_main:
    st.write("📰 메인 콘텐츠 영역 — 비율 3")
    st.code("col_main, col_side = st.columns([3, 1])")
with col_side:
    st.write("🧭 사이드 영역 — 비율 1")

st.subheader("2-3. 탭")
tab_chat, tab_doc, tab_stat = st.tabs(["💬 챗", "📄 문서", "📊 통계"])
with tab_chat:
    st.write("챗봇 인터페이스 자리")
with tab_doc:
    st.write("업로드된 문서 목록 자리")
with tab_stat:
    st.write("사용 통계 대시보드 자리")

st.divider()

# =============================================================================
# 3. 입력 위젯
# =============================================================================
st.header("3. 입력 위젯")

iw1, iw2 = st.columns(2)
with iw1:
    name = st.text_input("이름을 입력하세요", placeholder="홍길동")
    message = st.text_area("긴 텍스트 입력", height=120, placeholder="여러 줄 입력...")
    age = st.number_input("나이", min_value=1, max_value=120, value=25)
    date = st.date_input("날짜 선택")
with iw2:
    model = st.selectbox(
        "모델 선택",
        ["gpt-4o", "claude-3.5-sonnet", "llama-3.1-70b"],
    )
    models = st.multiselect(
        "비교 모델 선택 (복수 선택 가능)",
        ["gpt-4o", "claude-3.5-sonnet", "llama-3.1-70b"],
        default=["gpt-4o"],
    )
    temp = st.slider("Temperature", 0.0, 1.0, 0.7, step=0.1)
    debug = st.checkbox("Debug 모드 활성화")
    theme = st.radio("테마", ["라이트", "다크"], horizontal=True)

if st.button("🚀 실행", type="primary"):
    st.success(
        f"안녕하세요, **{name or '익명'}**님! "
        f"선택 모델: `{model}` / 온도: `{temp}` / 비교 모델: {models or '없음'}"
    )
    if debug:
        st.json({
            "name": name, "message": message, "age": age,
            "date": str(date), "model": model, "models": models,
            "temperature": temp, "theme": theme,
        })

st.divider()

# =============================================================================
# 4. session_state 데모 — 카운터
# =============================================================================
st.header("4. session_state 패턴 — 카운터")
st.write(
    "Streamlit은 위젯 인터랙션마다 스크립트를 **처음부터 끝까지 재실행**합니다. "
    "값을 유지하려면 `st.session_state`에 저장해야 합니다."
)

sc1, sc2, sc3, sc4 = st.columns([1, 1, 1, 3])
with sc1:
    if st.button("➕ +1"):
        st.session_state.count += 1
with sc2:
    if st.button("➖ -1"):
        st.session_state.count -= 1
with sc3:
    if st.button("🔄 Reset"):
        st.session_state.count = 0
with sc4:
    st.metric("Counter", st.session_state.count)

with st.expander("🔍 현재 session_state 전체 보기"):
    st.json({k: str(v) for k, v in st.session_state.items()})
