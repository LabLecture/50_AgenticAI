"""Documents 페이지 — 파일 업로드 및 컨텍스트 등록."""
import streamlit as st

from components.sidebar import render_common_sidebar

st.set_page_config(page_title="Documents", page_icon="📄", layout="wide")
render_common_sidebar()

st.title("📄 Documents")
st.write(
    "업로드된 파일은 컨텍스트로 등록되어 **Chat 페이지**의 모든 응답에 자동 반영됩니다."
)

uploaded = st.file_uploader(
    "파일을 업로드하세요",
    type=["pdf", "txt", "md", "csv"],
    accept_multiple_files=False,
)

if uploaded is not None:
    st.success(f"✅ **{uploaded.name}** ({uploaded.size / 1024:.1f} KB)")
    file_name_lower = uploaded.name.lower()
    extracted = ""

    if file_name_lower.endswith((".txt", ".md")):
        extracted = uploaded.read().decode("utf-8", errors="replace")

    elif file_name_lower.endswith(".pdf"):
        import fitz

        with st.status("📚 PDF 처리", expanded=True) as s:
            doc = fitz.open(stream=uploaded.read(), filetype="pdf")
            n = len(doc)
            st.write(f"총 {n}페이지")
            bar = st.progress(0.0, text="페이지 0")
            chunks = []
            for i, page in enumerate(doc):
                chunks.append(page.get_text())
                bar.progress((i + 1) / n, text=f"페이지 {i + 1} / {n}")
            bar.empty()
            extracted = "\n".join(chunks)
            s.update(label="✅ 추출 완료", state="complete", expanded=False)

    elif file_name_lower.endswith(".csv"):
        import pandas as pd

        df = pd.read_csv(uploaded)
        st.dataframe(df.head(10), use_container_width=True)
        st.caption(f"shape: **{df.shape[0]}행 × {df.shape[1]}열**")
        extracted = df.to_string()

    if extracted:
        st.session_state.uploaded_context = extracted
        st.info(f"💡 컨텍스트 등록 완료 — {len(extracted):,}자")
        with st.expander("📄 미리보기"):
            st.text_area("앞 1000자", extracted[:1000], height=200, disabled=True)

st.divider()

# ─ 현재 등록된 컨텍스트 관리 ─
st.subheader("📦 현재 등록된 컨텍스트")
ctx = st.session_state.uploaded_context
if ctx:
    st.success(f"등록됨 — 총 {len(ctx):,}자")
    with st.expander("내용 보기"):
        st.text_area("context", ctx[:2000], height=200, disabled=True)
    if st.button("🗑 컨텍스트 비우기"):
        st.session_state.uploaded_context = ""
        st.rerun()
else:
    st.info("아직 등록된 컨텍스트가 없습니다.")
