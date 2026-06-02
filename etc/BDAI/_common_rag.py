"""
RAG 실습 공통 모듈 — 샘플 문서, 임베딩/LLM/벡터스토어 헬퍼.

각 rag0X.py 에서 import 해서 사용한다.

설계 결정
---------
* 임베딩 : 로컬 HuggingFace `intfloat/multilingual-e5-small` (한국어 OK, ~470MB)
           → OpenAI API 키가 필요 없도록 구성. 강의안의 OpenAIEmbeddings 와 동등 역할.
* LLM    : OpenRouter (OpenAI 호환) 를 사용. `OPENROUTER_API_KEY` 가 없으면 None 반환.
* 벡터스토어: 인메모리 Chroma (영구 디렉토리 사용 안 함, 매 실행마다 새로 생성)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable

# Windows cp949 대비
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# .env 자동 로드 — BDAI/.env 의 OPENROUTER_API_KEY / OPENAI_API_KEY / COHERE_API_KEY 등을
# os.environ 에 주입한다. python-dotenv 가 없는 환경에서도 죽지 않게 graceful 처리.
# 이미 환경변수가 설정돼 있으면 override 하지 않음 (`override=False` 가 기본값).
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

from langchain_core.documents import Document

# ---------------------------------------------------------------------------
# 샘플 한국어 문서 (AI / RAG / 검색 도메인)
# ---------------------------------------------------------------------------
SAMPLE_DOCS: list[Document] = [
    Document(
        page_content=(
            "벡터 검색은 텍스트를 고차원 임베딩 벡터로 변환한 뒤 코사인 유사도 같은 "
            "지표로 가까운 문서를 찾는 검색 방식이다. 의미가 유사하면 단어가 달라도 "
            "검색되지만, 정확한 키워드 일치는 약하다."
        ),
        metadata={"id": "doc01", "topic": "vector_search"},
    ),
    Document(
        page_content=(
            "BM25 는 단어 빈도와 문서 길이를 고려해 점수를 매기는 전통적인 키워드 검색 "
            "알고리즘이다. 정확한 단어 일치에 강하고 인덱싱이 빠르지만, 동의어나 의미 "
            "유사성은 잡지 못한다."
        ),
        metadata={"id": "doc02", "topic": "bm25"},
    ),
    Document(
        page_content=(
            "하이브리드 검색은 BM25 같은 sparse 검색과 임베딩 기반 dense 검색을 결합해 "
            "각자의 약점을 보완한다. 두 결과의 점수를 가중 합산하거나 reciprocal rank "
            "fusion(RRF) 같은 방법으로 통합한다."
        ),
        metadata={"id": "doc03", "topic": "hybrid_search"},
    ),
    Document(
        page_content=(
            "Cross-Encoder 리랭커는 질의와 문서를 함께 입력 받아 관련성 점수를 직접 계산하는 "
            "모델이다. 1차 검색이 추려준 후보 20~100개를 정밀하게 재정렬해 Top-K 품질을 "
            "크게 끌어올린다. 비용이 비싸 1차 검색에는 쓰지 않는다."
        ),
        metadata={"id": "doc04", "topic": "reranking"},
    ),
    Document(
        page_content=(
            "Cohere Rerank API 는 다국어를 지원하는 상용 리랭커 서비스다. "
            "rerank-multilingual-v3.0 모델은 한국어를 포함한 100개 이상 언어를 처리한다. "
            "API 호출 비용이 발생하므로 후보 수와 호출 빈도를 관리해야 한다."
        ),
        metadata={"id": "doc05", "topic": "cohere"},
    ),
    Document(
        page_content=(
            "MultiQueryRetriever 는 LLM 으로 원본 질의를 여러 표현으로 다시 작성한 뒤, "
            "각각의 변형 질의로 검색을 수행하고 결과를 합집합으로 결합한다. 사용자의 짧은 "
            "질의를 다양한 각도로 풀어내어 검색 누락을 줄인다."
        ),
        metadata={"id": "doc06", "topic": "query_transformation"},
    ),
    Document(
        page_content=(
            "컨텍스트 압축은 검색된 문서 전문을 그대로 LLM 에 넣지 않고, 질의와 관련된 "
            "문장만 추출해 토큰 비용을 절약하는 기법이다. LLMChainExtractor 는 LLM "
            "자체에게 관련 부분 추출을 맡기는 방식이다."
        ),
        metadata={"id": "doc07", "topic": "context_compression"},
    ),
    Document(
        page_content=(
            "RAG 의 청크 분할 전략은 검색 품질에 큰 영향을 준다. 너무 잘게 자르면 맥락이 "
            "끊기고, 너무 크게 잡으면 검색 정확도가 떨어진다. 일반적으로 500~1500 토큰 "
            "범위에서 의미 단위로 자르고, 200 정도의 오버랩을 둔다."
        ),
        metadata={"id": "doc08", "topic": "chunking"},
    ),
    Document(
        page_content=(
            "프롬프트 인젝션은 사용자 입력에 포함된 악의적 지시문이 시스템 프롬프트나 "
            "검색된 문서에 섞여 들어가 LLM 의 행동을 조작하는 보안 위협이다. RAG 시스템은 "
            "외부 문서를 컨텍스트로 주입하므로 특히 주의가 필요하다."
        ),
        metadata={"id": "doc09", "topic": "security"},
    ),
    Document(
        page_content=(
            "LangChain 1.x 부터 일부 retriever 가 langchain.retrievers 에서 "
            "langchain_classic.retrievers 로 이동했다. 0.x 에서 작성된 코드는 import "
            "경로를 수정해야 동작한다. EnsembleRetriever, MultiQueryRetriever, "
            "ContextualCompressionRetriever 가 대표적이다."
        ),
        metadata={"id": "doc10", "topic": "langchain_migration"},
    ),
]


# ---------------------------------------------------------------------------
# 임베딩
# ---------------------------------------------------------------------------
_EMBEDDINGS = None


def get_embeddings():
    """로컬 HuggingFace 임베딩. 첫 호출 시 모델을 다운로드(~470MB)."""
    global _EMBEDDINGS
    if _EMBEDDINGS is None:
        from langchain_huggingface import HuggingFaceEmbeddings

        _EMBEDDINGS = HuggingFaceEmbeddings(
            model_name="intfloat/multilingual-e5-small",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _EMBEDDINGS


# ---------------------------------------------------------------------------
# 벡터스토어 (인메모리 Chroma)
# ---------------------------------------------------------------------------
def get_vectorstore(docs: Iterable[Document] | None = None):
    """매 호출마다 새 인메모리 Chroma 컬렉션을 만들어 반환."""
    from langchain_chroma import Chroma

    docs = list(docs) if docs is not None else SAMPLE_DOCS
    return Chroma.from_documents(
        documents=docs,
        embedding=get_embeddings(),
        collection_name="bdai_rag_demo",
    )


# ---------------------------------------------------------------------------
# LLM (OpenRouter / OpenAI 호환)
# ---------------------------------------------------------------------------
def get_llm(model: str | None = None, temperature: float = 0):
    """OPENROUTER_API_KEY 또는 OPENAI_API_KEY 가 있으면 ChatOpenAI 반환, 없으면 None.

    모델 선택 우선순위:
      1) 함수 인자 model
      2) 환경변수 OPENROUTER_MODEL (또는 OpenAI 직접 사용 시 OPENAI_MODEL)
      3) 기본값 — OpenRouter 의 비교적 안정적인 free 모델

    참고: OpenRouter free 모델은 upstream provider 의 quota 를 공유하므로 시점에 따라
    429 Too Many Requests 가 자주 발생한다. .env 의 `OPENROUTER_MODEL` 로 다른 free
    모델로 갈아탈 수 있게 구성. 또한 ChatOpenAI 의 max_retries 로 일시적 429/5xx 를
    자동 재시도.
    """
    from langchain_openai import ChatOpenAI

    if api_key := os.getenv("OPENROUTER_API_KEY"):
        # 기본 모델: openai/gpt-oss-20b:free
        # — 강의 실습 시점에 OpenRouter 상에서 가장 안정적으로 응답하던 free 모델.
        # — google/gemma-4-31b-it:free / meta-llama/llama-3.3-70b-instruct:free 등
        #   인기 free 모델은 업스트림 provider 의 공유 quota 가 자주 소진돼 429 가 잦음.
        # 다른 모델을 쓰려면 .env 에서 OPENROUTER_MODEL=... 로 덮어쓰기:
        #   qwen/qwen3-next-80b-a3b-instruct:free, openai/gpt-oss-120b:free,
        #   z-ai/glm-4.5-air:free, google/gemma-4-31b-it:free 등.
        chosen = (
            model
            or os.getenv("OPENROUTER_MODEL")
            or "openai/gpt-oss-20b:free"
        )
        return ChatOpenAI(
            model=chosen,
            temperature=temperature,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            max_retries=3,   # 일시적 429/5xx 는 exponential backoff 로 자동 재시도
            timeout=60,
        )
    if api_key := os.getenv("OPENAI_API_KEY"):
        chosen = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        # OpenAI 직접 호출 시 모델명에서 provider 접두어 제거
        clean_model = chosen.split("/", 1)[-1]
        return ChatOpenAI(
            model=clean_model,
            temperature=temperature,
            api_key=api_key,
            max_retries=3,
            timeout=60,
        )
    return None


# ---------------------------------------------------------------------------
# 출력 헬퍼
# ---------------------------------------------------------------------------
def print_results(title: str, docs: Iterable[Document], query: str | None = None) -> None:
    print("\n" + "=" * 70)
    print(f"📌 {title}")
    if query:
        print(f"🔍 query: {query}")
    print("=" * 70)
    for i, d in enumerate(docs, 1):
        topic = d.metadata.get("topic", "-")
        doc_id = d.metadata.get("id", "-")
        preview = d.page_content[:80].replace("\n", " ")
        print(f"  {i:2d}. [{doc_id} / {topic}] {preview}...")


def llm_unavailable_notice(feature: str) -> None:
    print("\n" + "─" * 70)
    print(f"⚠️  {feature} 는 LLM 호출이 필요합니다.")
    print("    OPENROUTER_API_KEY 또는 OPENAI_API_KEY 가 설정되어 있지 않아 스킵합니다.")
    print("    예: $env:OPENROUTER_API_KEY = 'sk-or-...'")
    print("─" * 70)
