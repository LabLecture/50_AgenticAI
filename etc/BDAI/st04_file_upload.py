"""
st04_file_upload.py — 파일 업로드 + 로딩 UX + LLM 컨텍스트 주입
강의안 섹션 2-5, 2-6 대응

지원 형식: TXT, MD, PDF, CSV
실행:
    streamlit run streamlit_practice/st04_file_upload.py
"""
import os
import time
import streamlit as st

st.set_page_config(page_title="St04 File Upload", page_icon="📄", layout="wide")

# =============================================================================
# 0. session_state
# =============================================================================
if "uploaded_context" not in st.session_state:
    st.session_state.uploaded_context = ""
if "messages" not in st.session_state:
    st.session_state.messages = []

# =============================================================================
# 1. 파일 업로드 UI
# =============================================================================
st.title("📄 파일 업로드 + 컨텍스트 주입 데모")

uploaded = st.file_uploader(
    "파일을 업로드하세요",
    type=["pdf", "txt", "md", "csv"],
    accept_multiple_files=False,
    help="지원 형식: PDF, TXT, MD, CSV (최대 200MB)",
)

# =============================================================================
# 2. 업로드 처리 (형식별 분기)
# =============================================================================
if uploaded is not None:
    info_col, _ = st.columns([2, 1])
    with info_col:
        st.success(
            f"✅ **{uploaded.name}** ({uploaded.size / 1024:.1f} KB) 업로드 완료"
        )

    extracted_text = ""
    file_type = uploaded.type or ""
    file_name_lower = uploaded.name.lower()

    # ── 텍스트 / 마크다운 ─────────────────────
    if file_type in ("text/plain", "text/markdown") or file_name_lower.endswith((".txt", ".md")):
        with st.spinner("📖 텍스트 읽는 중..."):
            extracted_text = uploaded.read().decode("utf-8", errors="replace")
        with st.expander("📄 파일 내용 미리보기", expanded=True):
            st.text_area(
                "본문 (앞 1000자)",
                extracted_text[:1000],
                height=200,
                disabled=True,
            )

    # ── PDF ─────────────────────────────────
    elif file_type == "application/pdf" or file_name_lower.endswith(".pdf"):
        import fitz  # PyMuPDF

        # st.status로 단계별 진행 표시
        with st.status("📚 PDF 처리 파이프라인", expanded=True) as status:
            st.write("📂 PDF 파일 열기...")
            doc = fitz.open(stream=uploaded.read(), filetype="pdf")
            page_count = len(doc)
            st.write(f"✅ 총 {page_count}페이지 확인")

            st.write("📝 텍스트 추출 중...")
            progress_bar = st.progress(0.0, text="페이지 0 / ?")
            pages_text = []
            for i, page in enumerate(doc):
                pages_text.append(page.get_text())
                pct = (i + 1) / page_count
                progress_bar.progress(pct, text=f"페이지 {i + 1} / {page_count}")
            progress_bar.empty()

            extracted_text = "\n".join(pages_text)
            st.write(f"✅ 추출 완료 — {len(extracted_text):,}자")
            status.update(label="✅ PDF 처리 완료!", state="complete", expanded=False)

        st.info(f"📑 총 {page_count}페이지 / 추출 텍스트 {len(extracted_text):,}자")
        with st.expander("📄 추출 텍스트 미리보기"):
            st.text_area(
                "본문 (앞 1000자)",
                extracted_text[:1000],
                height=200,
                disabled=True,
            )

    # ── CSV ─────────────────────────────────
    elif file_type == "text/csv" or file_name_lower.endswith(".csv"):
        import pandas as pd

        with st.spinner("📊 CSV 읽는 중..."):
            df = pd.read_csv(uploaded)
        st.subheader("미리보기 (상위 10행)")
        st.dataframe(df.head(10), use_container_width=True)
        st.caption(f"shape: **{df.shape[0]}행 × {df.shape[1]}열**")
        extracted_text = df.to_string()

    else:
        st.error(f"지원하지 않는 파일 형식입니다: {file_type or '(unknown)'}")

    # session_state에 저장
    if extracted_text:
        st.session_state.uploaded_context = extracted_text
        st.info("💡 파일 내용이 대화 컨텍스트에 저장되었습니다.")

# =============================================================================
# 3. 로딩 UX 패턴 데모
# =============================================================================
st.divider()
st.header("⏳ 로딩 UX 패턴 모음")

ux1, ux2, ux3 = st.columns(3)

with ux1:
    st.subheader("① st.spinner")
    if st.button("Spinner 실행", key="spinner"):
        with st.spinner("🔍 처리 중..."):
            time.sleep(1.5)
        st.success("완료!")

with ux2:
    st.subheader("② st.progress")
    if st.button("Progress 실행", key="progress"):
        bar = st.progress(0, text="시작...")
        for i in range(20):
            time.sleep(0.05)
            bar.progress((i + 1) / 20, text=f"처리 중 {i + 1}/20")
        bar.empty()
        st.success("완료!")

with ux3:
    st.subheader("③ st.status")
    if st.button("Status 실행", key="status"):
        with st.status("📚 RAG 파이프라인 시뮬레이션", expanded=True) as s:
            st.write("🔍 문서 검색 중...")
            time.sleep(0.5)
            st.write("🔄 리랭킹 중...")
            time.sleep(0.5)
            st.write("🤖 LLM 응답 생성 중...")
            time.sleep(0.5)
            s.update(label="✅ 완료!", state="complete", expanded=False)

# =============================================================================
# 4. 컨텍스트 주입 메시지 빌더 (참고용)
# =============================================================================
st.divider()
st.header("🧩 컨텍스트 주입 빌더")
st.write("업로드된 파일 내용을 시스템 메시지로 변환해 LLM 호출에 주입하는 패턴입니다.")

def build_messages_with_context(user_input: str, max_chars: int = 4000) -> list:
    messages = list(st.session_state.messages)
    if ctx := st.session_state.uploaded_context:
        context_msg = {
            "role": "system",
            "content": f"다음 문서 내용을 참고하여 답변하세요:\n\n{ctx[:max_chars]}",
        }
        messages = [context_msg] + messages
    messages.append({"role": "user", "content": user_input})
    return messages

if st.button("👀 빌더 결과 미리보기"):
    sample = build_messages_with_context("이 문서의 핵심 내용을 요약해줘")
    st.json(
        [
            {"role": m["role"], "content_preview": m["content"][:200]}
            for m in sample
        ]
    )
