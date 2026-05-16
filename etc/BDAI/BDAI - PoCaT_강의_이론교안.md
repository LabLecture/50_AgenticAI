# [A] 강의 이론 교안
## 프로젝트 실습 강의 — 이론 파트 (6일 × 4시간)

> **범례**
> - `[B] 교안 보강 예정` : 별도 Agent 강의 교안([B])에서 발췌·병합 예정
> - `> [이미지: ...]` : 실제 캡처/삽입 이미지 자리 표시자
> - `# ~~~ 실습소스 ~~~` : 실습 소스 코드 자리 표시자

---

## 1일차 (이론 2H) — LangGraph & LangManus (Multi-Agent)

### 1-1. Local LLM 서빙 (HuggingFace / ollama / vLLM)

> [B] 교안 보강 예정

---

### 1-2. OpenRouter를 통한 LLM API 연동

#### 개요

OpenRouter는 다양한 LLM 공급자(OpenAI, Anthropic, Google, Meta 등)의 모델을 **단일 API 엔드포인트**로 통합 제공하는 라우팅 플랫폼입니다.  
모델별 개별 API 키 관리 없이, OpenRouter 키 하나로 수십 개 모델을 전환·비교할 수 있습니다.

> [이미지: OpenRouter 홈페이지 — 지원 모델 목록 및 가격 비교 화면]

#### 핵심 특징

| 항목 | 내용 |
|------|------|
| 엔드포인트 | `https://openrouter.ai/api/v1` |
| 호환 방식 | OpenAI SDK 호환 (drop-in replacement) |
| 주요 지원 모델 | GPT-4o, Claude 3.x, Gemini 1.5, Llama 3, Mistral, Qwen 등 |
| 비용 | 모델별 토큰 단가 과금 (무료 티어 일부 제공) |
| 기능 | 모델 fallback, 프롬프트 캐싱, 사용량 대시보드 |

#### 연동 방법 — Python (OpenAI SDK 호환)

```python
# ~~~ 실습소스: OpenRouter 기본 연동 ~~~
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="<OPENROUTER_API_KEY>",
)

response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",          # 모델 슬러그
    messages=[
        {"role": "user", "content": "안녕하세요!"}
    ],
    extra_headers={
        "HTTP-Referer": "https://your-app.com",   # 선택: 출처 헤더
        "X-Title": "My App",                       # 선택: 앱 이름
    }
)
print(response.choices[0].message.content)
```

#### LangChain 연동

```python
# ~~~ 실습소스: OpenRouter + LangChain ChatOpenAI ~~~
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="meta-llama/llama-3.1-70b-instruct",
    openai_api_key="<OPENROUTER_API_KEY>",
    openai_api_base="https://openrouter.ai/api/v1",
)

result = llm.invoke("LangGraph를 한 줄로 설명해줘")
print(result.content)
```

> [이미지: OpenRouter 대시보드 — 사용량 및 비용 모니터링 화면]

#### 모델 선택 전략

- **개발/테스트 단계** : 무료 티어 모델(`meta-llama/llama-3.1-8b-instruct:free`) 활용
- **품질 중심 프로덕션** : `anthropic/claude-3.5-sonnet` 또는 `openai/gpt-4o`
- **비용 최적화** : `google/gemini-flash-1.5` (속도·비용 균형)
- **Fallback 설정** : 주 모델 오류 시 대체 모델 자동 전환 (`models` 배열 지정)

```python
# ~~~ 실습소스: OpenRouter Fallback 모델 설정 ~~~
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[...],
    extra_body={
        "models": [
            "openai/gpt-4o",
            "anthropic/claude-3.5-sonnet",   # fallback 1
            "google/gemini-1.5-pro",          # fallback 2
        ]
    }
)
```

---

### 1-3. FrontEnd / BackEnd 구조

> [B] 교안 보강 예정

---

### 1-4. RDB 연동 (PostgreSQL)

> [B] 교안 보강 예정

---

### 1-5. LangGraph & LangManus 이론

> [B] 교안 보강 예정

---

## 2일차 (이론 1H) — Streamlit 기초 + UI 구현

### 2-1. Streamlit 개요

Streamlit은 Python 코드만으로 **대화형 웹 앱**을 빠르게 구축할 수 있는 오픈소스 프레임워크입니다.  
별도의 HTML/CSS/JavaScript 없이 LLM 챗봇, 데이터 대시보드, AI 데모 앱을 수 분 안에 배포할 수 있습니다.

> [이미지: Streamlit 공식 홈페이지 — 갤러리 화면]

#### Streamlit vs. 다른 프레임워크 비교

| 항목 | Streamlit | Gradio | FastAPI + React |
|------|-----------|--------|-----------------|
| 학습 곡선 | 낮음 (Python only) | 낮음 | 높음 (FE/BE 분리) |
| 프로토타이핑 속도 | 매우 빠름 | 빠름 | 느림 |
| 커스터마이징 | 중간 | 낮음 | 매우 높음 |
| 프로덕션 적합성 | 중간 | 낮음 | 높음 |
| LLM 챗 UI 지원 | 네이티브 지원 | 네이티브 지원 | 직접 구현 |

**→ 수업 프로젝트 수준에서는 Streamlit이 최적의 선택**

#### 설치 및 실행

```bash
# ~~~ 실습소스: Streamlit 설치 및 기본 실행 ~~~
pip install streamlit

# 앱 실행
streamlit run app.py

# 브라우저 자동 오픈: http://localhost:8501
# 코드 수정 시 자동 핫리로드 (저장하면 즉시 반영)
```

#### Streamlit의 렌더링 모델

```
코드 변경 or 위젯 인터랙션
        │
        ▼
   스크립트 전체 재실행 (top-to-bottom)
        │
        ▼
   st.session_state 유지 → 변경된 부분만 UI 갱신
```

> **핵심 원칙** : Streamlit은 상태 변화가 생길 때마다 스크립트를 **처음부터 끝까지 재실행**합니다.  
> 따라서 대화 히스토리, 설정값 등 유지가 필요한 데이터는 반드시 `st.session_state`에 저장해야 합니다.

#### st.session_state 핵심 사용법

`session_state`는 사용자별 서버 세션 동안 유지되는 딕셔너리입니다.

```python
# ~~~ 실습소스: session_state 기본 패턴 ~~~
import streamlit as st

# 초기화 패턴 (재실행 시 덮어쓰지 않도록 반드시 조건 체크)
if "count" not in st.session_state:
    st.session_state.count = 0

if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_model" not in st.session_state:
    st.session_state.selected_model = "anthropic/claude-3.5-sonnet"

# 읽기
print(st.session_state.count)
print(st.session_state["count"])   # 딕셔너리 방식도 동일

# 쓰기
st.session_state.count += 1
st.session_state["messages"].append({"role": "user", "content": "안녕"})

# 삭제
del st.session_state["count"]

# 강제 재실행 (상태 변경 후 UI 즉시 갱신)
st.rerun()
```

> [이미지: Streamlit 렌더링 흐름 다이어그램]

---

### 2-2. 기본 컴포넌트

#### 텍스트 & 알림

```python
# ~~~ 실습소스: Streamlit 텍스트 & 알림 컴포넌트 ~~~
import streamlit as st

# 타이틀 계층
st.title("🤖 AI 챗봇")
st.header("2단계 헤더")
st.subheader("3단계 서브헤더")
st.caption("보조 설명 텍스트 (작은 글씨)")

# 내용 출력
st.write("일반 텍스트 또는 Markdown 렌더링 (파이썬 객체도 자동 출력)")
st.markdown("**굵게**, _기울임_, `인라인코드`, [링크](https://streamlit.io)")
st.code("print('Hello, Streamlit!')", language="python")

# 알림 박스
st.info("ℹ️ 안내 메시지")
st.warning("⚠️ 경고 메시지")
st.error("❌ 오류 메시지")
st.success("✅ 성공 메시지")

# 구분선
st.divider()
```

#### 레이아웃 — 컬럼 & 탭

```python
# ~~~ 실습소스: Streamlit 컬럼 & 탭 레이아웃 ~~~
import streamlit as st

# 2단 컬럼 분할
col1, col2 = st.columns(2)
with col1:
    st.metric("총 문서 수", "1,234", delta="+56")
with col2:
    st.metric("평균 응답 시간", "1.8s", delta="-0.3s")

# 비율 지정 컬럼 (3:1)
col_main, col_side = st.columns([3, 1])
with col_main:
    st.write("메인 콘텐츠 영역")
with col_side:
    st.write("사이드 영역")

# 탭
tab1, tab2, tab3 = st.tabs(["💬 챗", "📄 문서", "📊 통계"])
with tab1:
    st.write("챗봇 인터페이스")
with tab2:
    st.write("업로드된 문서 목록")
with tab3:
    st.write("사용 통계 대시보드")
```

#### 입력 위젯

```python
# ~~~ 실습소스: Streamlit 입력 위젯 ~~~
import streamlit as st

name    = st.text_input("이름을 입력하세요", placeholder="홍길동")
message = st.text_area("긴 텍스트 입력", height=150, placeholder="여러 줄 입력...")
age     = st.number_input("나이", min_value=1, max_value=120, value=25)
model   = st.selectbox("모델 선택", ["gpt-4o", "claude-3.5-sonnet", "llama-3.1-70b"])
models  = st.multiselect("비교 모델 선택", ["gpt-4o", "claude-3.5-sonnet", "llama-3.1-70b"])
temp    = st.slider("Temperature", 0.0, 1.0, 0.7, step=0.1)
debug   = st.checkbox("Debug 모드 활성화")
theme   = st.radio("테마", ["라이트", "다크"])
date    = st.date_input("날짜 선택")

if st.button("실행", type="primary"):   # type="primary" → 강조 버튼
    st.write(f"안녕하세요, {name}님! 선택 모델: {model}, 온도: {temp}")
```

> [이미지: Streamlit 위젯 전체 목록 화면 캡처]

---

### 2-3. st.chat_input / st.chat_message

LLM 챗봇 UI의 핵심 컴포넌트입니다.

| 컴포넌트 | 역할 |
|----------|------|
| `st.chat_input(placeholder)` | 화면 하단 고정 입력창. 엔터 or 전송 버튼으로 제출 |
| `st.chat_message(role)` | 말풍선 컨테이너. `role="user"` / `"assistant"` / `"system"` |

#### 기본 챗봇 구조

```python
# ~~~ 실습소스: Streamlit 챗봇 기본 구조 ~~~
import streamlit as st
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=st.secrets["OPENROUTER_API_KEY"],
)

st.title("🤖 AI 어시스턴트")

# 대화 히스토리 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 이전 대화 렌더링
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 사용자 입력
if prompt := st.chat_input("메시지를 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # LLM 응답
    with st.chat_message("assistant"):
        with st.spinner("생각 중..."):
            response = client.chat.completions.create(
                model="anthropic/claude-3.5-sonnet",
                messages=st.session_state.messages,
            )
            answer = response.choices[0].message.content
            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
```

#### 스트리밍 응답 처리 (st.write_stream)

단순 응답보다 **스트리밍**을 사용하면 첫 토큰이 즉시 표시되어 UX가 크게 향상됩니다.

```python
# ~~~ 실습소스: Streamlit 스트리밍 응답 ~~~
if prompt := st.chat_input("메시지를 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # 스트림 생성
        stream = client.chat.completions.create(
            model="anthropic/claude-3.5-sonnet",
            messages=st.session_state.messages,
            stream=True,   # 스트리밍 활성화
        )
        # st.write_stream이 토큰을 실시간으로 화면에 출력
        answer = st.write_stream(stream)

    st.session_state.messages.append({"role": "assistant", "content": answer})
```

> [이미지: Streamlit 챗봇 UI — 스트리밍 응답 화면 캡처]

#### 시스템 프롬프트 + 멀티턴 대화 관리

```python
# ~~~ 실습소스: 시스템 프롬프트 포함 멀티턴 구조 ~~~
SYSTEM_PROMPT = """당신은 친절한 AI 어시스턴트입니다.
사용자의 질문에 정확하고 간결하게 답변하세요.
한국어로 답변하세요."""

def get_llm_response(messages: list) -> str:
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    response = client.chat.completions.create(
        model="anthropic/claude-3.5-sonnet",
        messages=full_messages,
        max_tokens=2048,
        temperature=st.session_state.get("temperature", 0.7),
    )
    return response.choices[0].message.content
```

---

### 2-4. st.sidebar

사이드바는 **설정 패널, 모델 선택, 대화 관리** 등을 분리 배치할 때 사용합니다.

```python
# ~~~ 실습소스: Streamlit 사이드바 설정 패널 ~~~
import streamlit as st

with st.sidebar:
    st.header("⚙️ 설정")

    # 모델 선택
    st.session_state.selected_model = st.selectbox(
        "LLM 모델",
        [
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "meta-llama/llama-3.1-70b-instruct",
            "google/gemini-flash-1.5",
        ],
        index=0,
    )

    # 파라미터
    st.session_state.temperature = st.slider("Temperature", 0.0, 1.0, 0.7, step=0.05)
    st.session_state.max_tokens  = st.number_input("Max Tokens", 256, 8192, 2048, step=256)

    st.divider()

    # 시스템 프롬프트 커스터마이징
    with st.expander("🧠 시스템 프롬프트 편집"):
        st.session_state.system_prompt = st.text_area(
            "시스템 프롬프트",
            value="당신은 친절한 AI 어시스턴트입니다.",
            height=120,
        )

    st.divider()

    # 대화 관리
    st.subheader("💬 대화 관리")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑 초기화", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col2:
        # 대화 내보내기
        if st.session_state.get("messages"):
            import json
            history_json = json.dumps(st.session_state.messages, ensure_ascii=False, indent=2)
            st.download_button(
                "💾 저장",
                data=history_json,
                file_name="chat_history.json",
                mime="application/json",
                use_container_width=True,
            )

    st.divider()
    st.caption(f"총 대화 수: {len(st.session_state.get('messages', []))}")
```

> [이미지: Streamlit 사이드바 — 모델 선택 + 시스템 프롬프트 편집 화면]

---

### 2-5. 파일 업로드 기능 구현

#### 파일 업로드 기본 구조

```python
# ~~~ 실습소스: Streamlit 파일 업로드 + 다중 형식 처리 ~~~
import streamlit as st

uploaded = st.file_uploader(
    "파일을 업로드하세요",
    type=["pdf", "txt", "md", "csv"],
    accept_multiple_files=False,   # True로 변경 시 다중 업로드 가능
    help="지원 형식: PDF, TXT, MD, CSV (최대 200MB)",
)

if uploaded is not None:
    file_info_col, _ = st.columns([2, 1])
    with file_info_col:
        st.success(f"✅ **{uploaded.name}** ({uploaded.size / 1024:.1f} KB) 업로드 완료")

    # ── 텍스트 파일 처리 ──────────────────────────
    if uploaded.type in ("text/plain", "text/markdown"):
        content = uploaded.read().decode("utf-8")
        with st.expander("📄 파일 내용 미리보기"):
            # ⚠️ Streamlit 1.27+ : label="" 은 접근성 경고. label_visibility="collapsed" 로 숨김.
            st.text_area("미리보기", content[:1000], height=200, disabled=True,
                         label_visibility="collapsed")
        st.session_state["uploaded_context"] = content

    # ── PDF 처리 (PyMuPDF) ────────────────────────
    elif uploaded.type == "application/pdf":
        import fitz  # pip install pymupdf
        with st.spinner("📖 PDF 텍스트 추출 중..."):
            doc  = fitz.open(stream=uploaded.read(), filetype="pdf")
            text = "\n".join([page.get_text() for page in doc])
            page_count = len(doc)
        st.info(f"📑 총 {page_count}페이지 / 추출 텍스트 {len(text):,}자")
        with st.expander("📄 추출 텍스트 미리보기"):
            st.text_area("미리보기", text[:1000], height=200, disabled=True,
                         label_visibility="collapsed")
        st.session_state["uploaded_context"] = text

    # ── CSV 처리 ──────────────────────────────────
    elif uploaded.type == "text/csv":
        import pandas as pd
        df = pd.read_csv(uploaded)
        st.dataframe(df.head(10), use_container_width=True)
        st.session_state["uploaded_context"] = df.to_string()

    st.info("💡 파일 내용이 대화 컨텍스트에 추가되었습니다. 이제 파일에 대해 질문하세요!")
```

> [이미지: 파일 업로드 — PDF 업로드 후 텍스트 추출 미리보기 화면]

#### 업로드된 파일을 RAG 없이 LLM에 직접 전달하기

파일이 작은 경우(~수천 토큰), 벡터 DB 없이 전체 텍스트를 컨텍스트로 직접 주입할 수 있습니다.

```python
# ~~~ 실습소스: 파일 컨텍스트를 LLM에 직접 주입 ~~~
def build_messages_with_context(user_input: str) -> list:
    messages = list(st.session_state.messages)  # 기존 히스토리 복사

    # 업로드된 파일 컨텍스트가 있으면 시스템 메시지에 삽입
    if ctx := st.session_state.get("uploaded_context"):
        context_msg = {
            "role": "system",
            "content": f"다음 문서 내용을 참고하여 답변하세요:\n\n{ctx[:4000]}"
        }
        messages = [context_msg] + messages

    messages.append({"role": "user", "content": user_input})
    return messages
```

---

### 2-6. st.spinner / st.progress / 로딩 UX

사용자가 기다리는 동안 **진행 상태를 명확하게 표시**하는 것은 LLM 앱 UX의 핵심입니다.

```python
# ~~~ 실습소스: 로딩 UX 패턴 모음 ~~~
import streamlit as st
import time

# ① spinner — 작업 중 회전 아이콘 표시
with st.spinner("🔍 문서 분석 중..."):
    time.sleep(2)  # 실제 작업 대체

with st.spinner("🤖 LLM 응답 생성 중..."):
    response = call_llm(prompt)

# ② progress bar — 배치 작업 진행률 표시
progress_bar = st.progress(0, text="문서 청크 처리 중...")
for i, chunk in enumerate(chunks):
    process(chunk)
    pct = (i + 1) / len(chunks)
    progress_bar.progress(pct, text=f"처리 중... {i+1}/{len(chunks)}")
progress_bar.empty()   # 완료 후 바 숨기기

# ③ status — 단계별 작업 상태 표시 (Streamlit 1.28+)
with st.status("📚 RAG 파이프라인 실행 중...", expanded=True) as status:
    st.write("🔍 문서 검색 중...")
    docs = retriever.invoke(query)
    st.write(f"✅ {len(docs)}개 문서 검색 완료")

    st.write("🔄 리랭킹 중...")
    reranked = reranker.compress_documents(docs, query)
    st.write("✅ 리랭킹 완료")

    st.write("🤖 LLM 응답 생성 중...")
    answer = llm.invoke(build_prompt(reranked, query))
    status.update(label="✅ 완료!", state="complete", expanded=False)
```

> [이미지: st.status 단계별 진행 표시 화면 캡처]

---

### 2-7. 앱 전체 구조 — 파일 구성 권장 패턴

규모가 커지면 `app.py` 단일 파일 대신 아래 구조로 분리하는 것이 좋습니다.

```
project/
├── app.py                  # Streamlit 진입점 (페이지 라우팅)
├── pages/
│   ├── 1_💬_Chat.py        # 챗봇 페이지 (자동으로 사이드바 메뉴에 등록)
│   ├── 2_📄_Documents.py   # 문서 관리 페이지
│   └── 3_📊_Dashboard.py   # 모니터링 대시보드
├── components/
│   ├── sidebar.py          # 사이드바 컴포넌트 (공통)
│   └── chat_ui.py          # 챗 UI 헬퍼 함수
├── core/
│   ├── llm.py              # LLM 클라이언트 초기화
│   └── rag.py              # RAG 파이프라인
└── .streamlit/
    └── secrets.toml        # API 키 (git ignore 필수!)
```

**`pages/` 디렉토리 활용 — 멀티페이지 앱**

```python
# ~~~ 실습소스: app.py — 멀티페이지 진입점 ~~~
import streamlit as st

st.set_page_config(
    page_title="AI 프로젝트",
    page_icon="🤖",
    layout="wide",              # "centered" | "wide"
    initial_sidebar_state="expanded",
)

st.title("🤖 AI 프로젝트 홈")
st.write("사이드바에서 원하는 기능을 선택하세요.")
```

**secrets.toml — API 키 관리**

```toml
# ~~~ 실습소스: .streamlit/secrets.toml ~~~
# .gitignore에 반드시 추가: .streamlit/secrets.toml

OPENROUTER_API_KEY = "sk-or-..."
LANGFUSE_PUBLIC_KEY = "pk-lf-..."
LANGFUSE_SECRET_KEY = "sk-lf-..."
DATABASE_URL = "postgresql://..."
```

```python
# 코드에서 접근
api_key = st.secrets["OPENROUTER_API_KEY"]
```

> [이미지: Streamlit 멀티페이지 앱 — 사이드바 메뉴 자동 생성 화면]

---

## 3일차 (이론 1H) — 프로젝트 핵심 기능 구현

### 3-1. Langfuse (Cloud) 연동 및 Trace 처리

> [B] 교안 보강 예정

---

## 4일차 (이론 0H) — 팀별 중간 시연 + 피드백

> 이론 강의 없음 — 팀별 프로젝트 시연 및 강사 피드백 세션

---

## 5일차 (이론 1H) — 서비스 고도화 + 답변 품질 개선

### 5-1. 통신 프로토콜 표준화 (MCP / A2A / ACP)

> [B] 교안 보강 예정

---

### 5-2. RAG 검색 리랭킹 전략 및 품질 개선

> 📌 **LangChain 1.x 마이그레이션 주의**
> 본 절의 코드는 **langchain 1.x** 기준입니다. 0.x 부터 일부 retriever 의 패키지 위치가 바뀌었습니다.
> | 0.x | 1.x |
> |-----|-----|
> | `from langchain.retrievers import EnsembleRetriever` | `from langchain_classic.retrievers import EnsembleRetriever` |
> | `from langchain.retrievers import ContextualCompressionRetriever` | `from langchain_classic.retrievers import ContextualCompressionRetriever` |
> | `from langchain.retrievers.multi_query import MultiQueryRetriever` | `from langchain_classic.retrievers.multi_query import MultiQueryRetriever` |
> | `from langchain.retrievers.document_compressors import LLMChainExtractor` | `from langchain_classic.retrievers.document_compressors import LLMChainExtractor` |
> | `from langchain_community.vectorstores import Chroma` | `from langchain_chroma import Chroma` |
>
> 0.x 환경이라면 `langchain_classic` → `langchain` 으로, `langchain_chroma` → `langchain_community.vectorstores` 로 그대로 바꿔 사용하면 됩니다.

#### RAG 파이프라인 품질 문제의 원인

기본 RAG(Vector Search → LLM)의 한계:

```
질의 → Embedding 검색 → Top-K 청크 → LLM 생성
                  ↑
         ❌ 의미적 유사도 ≠ 답변에 실제로 유용한 문서
```

**주요 품질 저하 원인**

| 원인 | 설명 |
|------|------|
| 임베딩 공간의 의미 불일치 | 키워드는 같지만 맥락이 다른 문서 상위 노출 |
| Chunk 경계 문제 | 중요 정보가 청크 경계에서 잘림 |
| Top-K 고정 | 질문 복잡도와 무관하게 동일 개수 검색 |
| 검색 방식 단일화 | 벡터 검색만 사용, 키워드 검색 미활용 |

---

#### 전략 1 : 하이브리드 검색 (Hybrid Search)

벡터 검색(Dense)과 키워드 검색(Sparse, BM25)을 결합합니다.

```python
# ~~~ 실습소스: Hybrid Search (BM25 + Vector) ~~~
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever  # 1.x: langchain_classic
from langchain_chroma import Chroma                          # 1.x: langchain_chroma
from langchain_openai import OpenAIEmbeddings

# BM25 키워드 검색
bm25_retriever = BM25Retriever.from_documents(docs)
bm25_retriever.k = 5

# Vector 의미 검색
vectorstore = Chroma.from_documents(docs, OpenAIEmbeddings())
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# 앙상블 (가중치 조절 가능)
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.4, 0.6],   # BM25 40% + Vector 60%
)

results = ensemble_retriever.invoke("질의 텍스트")
```

> [이미지: Hybrid Search 아키텍처 다이어그램]

---

#### 전략 2 : 리랭킹 (Reranking)

1차 검색 결과(Top-K)를 **Cross-Encoder 모델**로 재평가하여 순위를 재조정합니다.

```
질의 + Top-20 문서
       │
       ▼  Cross-Encoder (정밀 관련성 평가)
       │
       ▼
재정렬된 Top-5 → LLM 컨텍스트
```

```python
# ~~~ 실습소스: Cohere Reranker 연동 ~~~
from langchain_cohere import CohereRerank
from langchain_classic.retrievers import ContextualCompressionRetriever  # 1.x: langchain_classic

# Cohere Reranker 설정
reranker = CohereRerank(
    cohere_api_key="<COHERE_API_KEY>",
    model="rerank-multilingual-v3.0",
    top_n=5,    # 최종 반환 문서 수
)

# 기존 retriever에 reranker 추가
compression_retriever = ContextualCompressionRetriever(
    base_compressor=reranker,
    base_retriever=ensemble_retriever,  # 1차 검색은 Top-20 반환
)

results = compression_retriever.invoke("질의 텍스트")
```

**무료 대안 — CrossEncoder (sentence-transformers)**

```python
# ~~~ 실습소스: 로컬 CrossEncoder 리랭킹 ~~~
from sentence_transformers import CrossEncoder

# ⚠️ ms-marco-MiniLM-L-6-v2 는 영어 학습 비중이 높아 한국어 점수가 평탄해질 수 있다.
#    한국어 위주라면 다음 모델을 권장:
#      - "Dongjin-kr/ko-reranker"           (~280MB, 한국어 학습)
#      - "BAAI/bge-reranker-v2-m3"          (~600MB, 다국어 강력)
model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

# 1차 검색 결과
candidates = retriever.invoke(query)

# 점수 계산 및 재정렬
pairs = [(query, doc.page_content) for doc in candidates]
scores = model.predict(pairs)

reranked = sorted(
    zip(scores, candidates),
    key=lambda x: float(x[0]),   # numpy scalar → float 캐스팅 권장
    reverse=True,
)
top_docs = [doc for _, doc in reranked[:5]]
```

> [이미지: Reranking 전후 검색 결과 비교 화면]

---

#### 전략 3 : 쿼리 변환 (Query Transformation)

사용자 질의를 LLM으로 재작성하거나 다각도 쿼리로 분해하여 검색 커버리지를 높입니다.

```python
# ~~~ 실습소스: MultiQueryRetriever — 질의 자동 확장 ~~~
from langchain_classic.retrievers.multi_query import MultiQueryRetriever  # 1.x: langchain_classic
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

multi_retriever = MultiQueryRetriever.from_llm(
    retriever=vector_retriever,
    llm=llm,
    # 기본값: 원본 질의 + 3개 변형 생성 후 합집합 검색
)

results = multi_retriever.invoke("RAG 성능을 높이는 방법은?")
# 내부 생성 질의 예시:
# - "RAG 시스템의 검색 정확도 개선 방안"
# - "Retrieval Augmented Generation 최적화 기법"
# - "LLM 답변 품질 향상을 위한 문서 검색 전략"
```

---

#### 전략 4 : 컨텍스트 압축 (Context Compression)

검색된 문서에서 **질의와 관련된 부분만 추출**하여 LLM 컨텍스트를 절약합니다.

```python
# ~~~ 실습소스: LLMChainExtractor 컨텍스트 압축 ~~~
from langchain_classic.retrievers.document_compressors import LLMChainExtractor  # 1.x
from langchain_classic.retrievers import ContextualCompressionRetriever          # 1.x

compressor = LLMChainExtractor.from_llm(llm)

compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=vector_retriever,
)

results = compression_retriever.invoke("질의 텍스트")
# 각 문서에서 질의 관련 문장만 추출하여 반환
```

---

#### 품질 개선 전략 요약

```
[기본 RAG]
질의 → Vector 검색(Top-5) → LLM

[고도화 RAG]
질의
  │
  ├─ Query 변환 (MultiQuery / HyDE)
  │
  ▼
Hybrid Search (BM25 + Vector, Top-20)
  │
  ▼
Reranking (Cross-Encoder, Top-5)
  │
  ▼
Context Compression
  │
  ▼
LLM 생성
```

> [이미지: 고도화 RAG 파이프라인 전체 아키텍처 다이어그램]

---

## 6일차 (이론 1H) — GitHub README + 기술 문서 작성

### 6-1. GitHub README 작성 가이드

#### README가 중요한 이유

README는 프로젝트의 **첫인상**입니다. 채용 담당자, 협업자, 오픈소스 기여자 모두 README를 통해 프로젝트의 가치를 판단합니다.

> [이미지: 잘 작성된 GitHub README 예시 화면]

#### README 필수 구성 요소

```markdown
# 프로젝트명 (+ 한 줄 설명)

[![Python](https://img.shields.io/badge/Python-3.11-blue)](...)
[![License](https://img.shields.io/badge/License-MIT-green)](...)

## 📌 프로젝트 소개
- 해결하는 문제 (What)
- 만든 이유 (Why)
- 핵심 기능 3줄 요약

## 🛠 기술 스택
| 분류 | 기술 |
|------|------|
| LLM | Claude 3.5 Sonnet, OpenRouter |
| Framework | LangGraph, LangChain |
| Frontend | Streamlit |
| Database | PostgreSQL, ChromaDB |
| Monitoring | Langfuse |

## 🚀 실행 방법
### 환경 설정
\`\`\`bash
git clone https://github.com/...
cd project-name
pip install -r requirements.txt
cp .env.example .env   # API 키 입력
\`\`\`

### 실행
\`\`\`bash
streamlit run app.py
\`\`\`

## 🏗 아키텍처
[시스템 구성도 이미지 또는 ASCII 다이어그램]

## 📊 주요 결과 / 성과 지표
- 응답 정확도: 기존 대비 35% 향상 (Ragas 평가 기준)
- 평균 응답 시간: 1.8초
- 처리 문서 수: PDF 최대 200페이지

## 📁 디렉토리 구조
\`\`\`
project/
├── app.py              # Streamlit 진입점
├── agents/             # LangGraph 에이전트
├── retriever/          # RAG 파이프라인
├── utils/              # 공통 유틸리티
└── tests/              # 테스트 코드
\`\`\`

## 🤝 팀원
| 이름 | 역할 | GitHub |
|------|------|--------|
| 홍길동 | AI 파이프라인 | @hong |
```

---

#### 아키텍처 다이어그램 작성 (Mermaid)

GitHub README에서 코드 블록으로 렌더링됩니다.

```mermaid
graph LR
    A[사용자] -->|질의| B[Streamlit UI]
    B --> C[LangGraph Agent]
    C --> D{라우팅}
    D -->|문서 검색| E[RAG Pipeline]
    D -->|일반 대화| F[LLM Direct]
    E --> G[(VectorDB)]
    E --> H[Reranker]
    H --> F
    F -->|응답| B
    C --> I[Langfuse Trace]
```

> [이미지: GitHub에서 Mermaid 다이어그램 렌더링 화면]

---

### 6-2. 기술 문서 작성

#### 문서화해야 할 핵심 항목

**API/함수 문서 (docstring)**

```python
# ~~~ 실습소스: 표준 docstring 작성 예시 ~~~
def retrieve_and_rerank(
    query: str,
    top_k: int = 5,
    rerank_model: str = "rerank-multilingual-v3.0"
) -> list[Document]:
    """
    하이브리드 검색 + 리랭킹으로 관련 문서를 반환합니다.

    Args:
        query: 사용자 검색 질의
        top_k: 최종 반환 문서 수 (기본값: 5)
        rerank_model: Cohere 리랭킹 모델명

    Returns:
        관련도 순으로 정렬된 Document 객체 리스트

    Raises:
        CohereAPIError: Reranker API 호출 실패 시

    Example:
        >>> docs = retrieve_and_rerank("LangGraph 사용법", top_k=3)
        >>> print(docs[0].page_content)
    """
```

**환경 변수 문서 (.env.example)**

```bash
# ~~~ 실습소스: .env.example 템플릿 ~~~
# LLM API
OPENROUTER_API_KEY=your_openrouter_api_key_here

# 모니터링
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com

# 데이터베이스
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# 선택: Reranker
COHERE_API_KEY=your_cohere_api_key_here
```

---

### 6-3. 이력서에 프로젝트 녹이는 방법

#### 기술 스택 단순 나열 → 문제 해결 스토리로

| ❌ 나쁜 예 | ✅ 좋은 예 |
|-----------|-----------|
| "LangGraph, RAG, Streamlit을 사용한 챗봇 개발" | "다단계 리랭킹 파이프라인 설계로 RAG 답변 정확도 35% 개선, 하이브리드 검색(BM25+Vector) 도입으로 키워드 질의 recall 향상" |
| "Multi-Agent 시스템 구현" | "LangGraph 기반 라우팅 에이전트 설계, 문서 검색/일반 대화/DB 조회를 목적에 맞게 자동 분기, 평균 응답 지연 1.2초 달성" |

#### STAR 포맷 프로젝트 기술

```
S (Situation)  : 기존 단일 LLM 호출 방식의 한계 — 복잡한 질의에서 할루시네이션 빈발
T (Task)       : Multi-Agent + RAG 아키텍처로 답변 신뢰도 향상
A (Action)     : LangGraph 상태 머신 설계, Cohere 리랭킹 도입, Langfuse 모니터링 구축
R (Result)     : 답변 정확도 35% 향상, 사용자 재질문율 40% 감소 (A/B 테스트 기준)
```

---

### 6-4. 성과 지표 정량화 방법

프로젝트 경험을 수치로 표현하면 신뢰도가 크게 높아집니다.

#### RAG 품질 측정 — Ragas 프레임워크

```python
# ~~~ 실습소스: Ragas 기본 평가 ~~~
from ragas import evaluate
from ragas.metrics import (
    faithfulness,       # 생성 답변이 컨텍스트에 충실한가
    answer_relevancy,   # 답변이 질문과 관련 있는가
    context_recall,     # 관련 문서를 빠짐없이 검색했는가
    context_precision,  # 검색 문서 중 실제 유용한 비율
)
from datasets import Dataset

data = {
    "question":   ["RAG란 무엇인가?", ...],
    "answer":     ["RAG는 ...", ...],
    "contexts":   [["관련 문서 1", "관련 문서 2"], ...],
    "ground_truth": ["정답 텍스트", ...],
}

dataset = Dataset.from_dict(data)
result  = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_recall, context_precision])
print(result)
# {'faithfulness': 0.87, 'answer_relevancy': 0.91, ...}
```

#### 측정 지표 체크리스트

| 지표 | 측정 방법 | 목표 기준 |
|------|-----------|-----------|
| 응답 정확도 | Ragas faithfulness/relevancy | > 0.85 |
| 평균 응답 시간 | Langfuse trace latency | < 3초 |
| 검색 Recall | Ragas context_recall | > 0.80 |
| 오류율 | Langfuse error 이벤트 비율 | < 2% |
| 사용자 만족도 | thumbs up/down 피드백 수집 | > 80% positive |

> [이미지: Langfuse 대시보드 — 응답 시간 및 품질 지표 모니터링 화면]

---

## 부록 — 참고 자료

| 주제 | URL |
|------|-----|
| OpenRouter 공식 문서 | https://openrouter.ai/docs |
| Streamlit 공식 문서 | https://docs.streamlit.io |
| LangChain 리트리버 | https://python.langchain.com/docs/modules/data_connection/retrievers |
| Ragas 평가 프레임워크 | https://docs.ragas.io |
| Cohere Rerank API | https://docs.cohere.com/docs/rerank-2 |
| Langfuse 공식 문서 | https://langfuse.com/docs |
| GitHub README 가이드 | https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes |

---

> **작성 기준일** : 2025년  
> **보강 예정 항목** : [B] 교안 병합, 실습 소스 코드 삽입, 캡처 이미지 추가
