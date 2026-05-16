# BDAI - PoCaT 실습

PoCaT 강의 실습 소스 (Streamlit + RAG).

| 시리즈 | 강의안 | 파일 prefix |
|--------|--------|-------------|
| Streamlit | `BDAI_-_PoCaT___Streamlit.md` (2-1 ~ 2-7) | `st01_` ~ `st05_` |
| RAG 검색 리랭킹 | `BDAI_-_5-2._RAG_.md` (5-2) | `rag01_` ~ `rag07_` |

## 환경 셋업

이 폴더는 **독립된 venv**를 사용합니다 (메인 프로젝트의 venv와 별개).

```powershell
cd BDAI
.\venv\Scripts\Activate.ps1

# (최초 1회) 의존성 설치
pip install -r requirements.txt
```

---

## ① Streamlit 실습

### 실행
```powershell
streamlit run st01_basics.py
streamlit run st02_chatbot.py
streamlit run st03_sidebar.py
streamlit run st04_file_upload.py

cd st05_multipage
streamlit run app.py
```

### 파일 구성
| 파일 | 강의안 섹션 | 핵심 학습 내용 |
|------|------------|--------------|
| `st01_basics.py` | 2-1, 2-2 | session_state · 텍스트/알림 · 컬럼/탭 · 입력 위젯 |
| `st02_chatbot.py` | 2-3 | 비스트리밍 · 스트리밍 · 멀티턴+시스템프롬프트 |
| `st03_sidebar.py` | 2-4 | 사이드바 설정 패널 · 파라미터 조정 · 대화 내보내기 |
| `st04_file_upload.py` | 2-5, 2-6 | TXT/MD/PDF/CSV 업로드 · 로딩 UX |
| `st05_multipage/` | 2-7 | 멀티페이지 앱 · components/core 분리 · secrets |

### 검증
```powershell
python _verify_apps.py        # HTTP startup 검증
python _verify_apptest.py     # AppTest in-process 검증
```

---

## ② RAG 검색 리랭킹 실습

### 실행
```powershell
python rag01_baseline.py             # 순수 Vector RAG (기준점)
python rag02_hybrid_search.py        # BM25 + Vector
python rag03_reranking_local.py      # 로컬 CrossEncoder 리랭킹
python rag04_reranking_cohere.py     # Cohere API (COHERE_API_KEY 필요)
python rag05_query_transformation.py # MultiQuery (LLM 키 필요)
python rag06_context_compression.py  # LLMChainExtractor (LLM 키 필요)
python rag07_full_pipeline.py        # 통합 파이프라인 (모든 전략 결합)
```

### 파일 구성
| 파일 | 전략 | 핵심 학습 내용 |
|------|-----|---------------|
| `_common_rag.py` | (공통) | 한국어 샘플 문서 10개 · 임베딩/벡터스토어/LLM 헬퍼 |
| `rag01_baseline.py` | — | 순수 Vector Search Top-5 (비교 기준) |
| `rag02_hybrid_search.py` | 1. Hybrid | BM25 + Vector EnsembleRetriever (가중치 비교 3종) |
| `rag03_reranking_local.py` | 2. Rerank (무료) | sentence-transformers CrossEncoder 로컬 |
| `rag04_reranking_cohere.py` | 2. Rerank (유료) | Cohere `rerank-multilingual-v3.0` |
| `rag05_query_transformation.py` | 3. Query 변환 | MultiQueryRetriever (LLM 자동 변형) |
| `rag06_context_compression.py` | 4. Context 압축 | LLMChainExtractor |
| `rag07_full_pipeline.py` | 통합 | Hybrid → MultiQuery → Rerank → Compress → LLM |

### 첫 실행 시 다운로드되는 모델
- `intfloat/multilingual-e5-small` 임베딩 (~470MB) — 모든 RAG 파일에서 사용
- `cross-encoder/ms-marco-MiniLM-L-6-v2` 리랭커 (~90MB) — rag03, rag07

### langchain 1.x 마이그레이션 주의
강의안은 langchain 0.x 기준입니다. 1.x 부터는 일부 retriever 가 이동했습니다.
| 0.x | 1.x |
|------|------|
| `from langchain.retrievers import EnsembleRetriever` | `from langchain_classic.retrievers import EnsembleRetriever` |
| `from langchain.retrievers import ContextualCompressionRetriever` | `from langchain_classic.retrievers import ContextualCompressionRetriever` |
| `from langchain.retrievers.multi_query import MultiQueryRetriever` | `from langchain_classic.retrievers.multi_query import MultiQueryRetriever` |
| `from langchain.retrievers.document_compressors import LLMChainExtractor` | `from langchain_classic.retrievers.document_compressors import LLMChainExtractor` |
| `from langchain_community.vectorstores import Chroma` | `from langchain_chroma import Chroma` |

각 rag0X 파일 상단에 원본 import 와 함께 주석으로 안내했습니다.

---

## API 키

| 키 | 어디서 쓰는가 | 없으면? |
|-----|--------------|--------|
| `OPENROUTER_API_KEY` 또는 `OPENAI_API_KEY` | st02~05 챗봇, rag05/06/07 의 LLM 호출 | st 앱은 정상 로드 후 입력 시점에 경고 / rag 는 graceful skip + 안내 |
| `COHERE_API_KEY` | rag04 만 | graceful skip + 안내 |

설정 예 (PowerShell):
```powershell
$env:OPENROUTER_API_KEY = "sk-or-..."
$env:COHERE_API_KEY = "..."
```
