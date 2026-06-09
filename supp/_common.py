"""
공통 헬퍼 — 모든 실습 스크립트에서 import 해서 쓴다.

설계 결정
---------
* LLM   : OpenRouter free 모델 (`openai/gpt-oss-20b:free`).
          `OPENROUTER_MODEL` 환경변수로 덮어쓰기 가능.
* 임베딩: HuggingFace `intfloat/multilingual-e5-small` (한국어 OK, OpenAI 키 불필요)
* 벡터DB: 인메모리 Chroma (매 실행마다 새로 생성)
* 웹검색: DuckDuckGo (`duckduckgo-search`). Tavily 키 없이도 동작.
* .env  : 모듈 import 시점에 자동 로드.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ── .env 자동 로드 ─────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

from langchain_core.documents import Document


# ===========================================================================
# 1) LLM
# ===========================================================================
def get_llm(temperature: float = 0):
    """OpenRouter free 모델 ChatOpenAI 반환. 키 없으면 None."""
    from langchain_openai import ChatOpenAI

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None

    # 기본: google/gemma-4-26b-a4b-it:free (2026-06-03 시점 가장 안정. 응답 깔끔, 한국어 OK).
    # 과거 openai/gpt-oss-20b:free 가 'no healthy upstream' (503) 으로 지속 장애.
    # 시점별 가용성 변동 가능 — .env 의 OPENROUTER_MODEL 로 언제든 교체.
    model = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash")
    # model = os.getenv("OPENROUTER_MODEL", "google/gemma-4-26b-a4b-it:free")
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        max_retries=3,
        timeout=60,
    )


def get_vlm(temperature: float = 0):
    """OpenRouter free Vision 모델 ChatOpenAI 반환 (supp_05 멀티모달용).

    `OPENROUTER_VISION_MODEL` env 로 덮어쓰기 가능.
    기본값: `google/gemma-4-31b-it:free` — image input 지원 확인된 free 모델.
    대안: `nvidia/nemotron-nano-12b-v2-vl:free`, `google/gemma-4-26b-a4b-it:free` 등.
    """
    from langchain_openai import ChatOpenAI

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None

    model = os.getenv("OPENROUTER_VISION_MODEL", "google/gemma-4-31b-it:free")
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        max_retries=3,
        timeout=90,   # 이미지 인코딩 추가 지연
    )


def structured(llm, schema):
    """구조화 출력 — free 모델 호환성을 위해 json_mode 사용.

    OpenRouter free 모델(gpt-oss, qwen 등) 은 default 인 function_calling
    이 불안정해서 텍스트 prefix 가 섞이거나 choices 가 None 인 응답이 종종 옴.
    json_mode 는 response_format={"type":"json_object"} 만 요구해서 더 호환성 좋음.

    ⚠ 호출하는 프롬프트의 system 메시지에 "JSON으로 출력하라" 가 들어가 있어야 함.
    """
    return llm.with_structured_output(schema, method="json_mode")


def binary_yesno(llm, system_msg: str, user_msg: str) -> str:
    """이진 yes/no 채점 — Pydantic / structured output 우회.

    free 모델(`gpt-oss-20b:free` 등) 의 structured output 은 schema 미준수
    응답(`{}`) 이 자주 나오므로, 단순 yes/no 판정은 plain text 로 받아 파싱.
    응답 어디든 'yes' 가 있으면 'yes', 그 외 'no' (보수적 디폴트).
    """
    from langchain_core.messages import SystemMessage, HumanMessage
    full_system = (
        system_msg
        + "\n\n응답은 정확히 'yes' 또는 'no' 한 단어 영어로만 출력하라. "
        + "다른 텍스트·JSON·설명·따옴표 금지."
    )
    resp = llm.invoke([SystemMessage(content=full_system),
                        HumanMessage(content=user_msg)])
    text = (resp.content or "").strip().lower()
    return "yes" if "yes" in text and "no" not in text[:20] else "no"


# ===========================================================================
# 2) 임베딩 + 샘플 문서 + 벡터스토어
# ===========================================================================
_EMB = None


def get_embeddings():
    """로컬 HuggingFace 임베딩 (최초 호출 시 ~470MB 다운로드)."""
    global _EMB
    if _EMB is None:
        from langchain_huggingface import HuggingFaceEmbeddings
        _EMB = HuggingFaceEmbeddings(
            model_name="intfloat/multilingual-e5-small",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _EMB


# ── 한국어 AI 에이전트/RAG 도메인 샘플 문서 (10개) ──────────────────
SAMPLE_DOCS: List[Document] = [
    Document(
        page_content=(
            "LLM 에이전트의 메모리는 크게 세 가지로 나뉜다. "
            "단기 메모리(short-term)는 현재 대화의 컨텍스트 윈도우이고, "
            "장기 메모리(long-term)는 벡터DB나 외부 저장소에 보관해 필요할 때 검색해 가져오며, "
            "감각 메모리(sensory)는 입력 직후의 매우 짧은 보존이다."
        ),
        metadata={"id": "doc01", "topic": "agent_memory"},
    ),
    Document(
        page_content=(
            "도구 사용(tool use)은 에이전트가 LLM의 한계를 보완하는 핵심 능력이다. "
            "함수 호출(function calling) 인터페이스로 검색·계산기·코드 실행·API 호출 등을 "
            "외부 도구로 분리하면 환각이 줄고 실시간 정보 접근이 가능해진다."
        ),
        metadata={"id": "doc02", "topic": "tool_use"},
    ),
    Document(
        page_content=(
            "복잡한 질문을 한 번에 풀 수 없을 때 에이전트는 계획(planning)을 세운다. "
            "Chain-of-Thought 는 단계적 추론을, ReAct 는 추론과 행동을 번갈아 수행하며, "
            "Tree of Thoughts 는 여러 경로를 동시에 탐색해 가장 좋은 답을 고른다."
        ),
        metadata={"id": "doc03", "topic": "planning"},
    ),
    Document(
        page_content=(
            "자기 성찰(self-reflection)은 에이전트가 자기 결과를 점검하고 개선하는 단계다. "
            "충실성(groundedness)은 답이 근거 문서에 의해 뒷받침되는지를 보고, "
            "유용성(usefulness)은 질문 의도를 실제로 만족하는지를 본다."
        ),
        metadata={"id": "doc04", "topic": "self_reflection"},
    ),
    Document(
        page_content=(
            "Naive RAG 는 질문을 임베딩해 벡터DB에서 top-k 청크를 검색하고 그대로 LLM 에 넣는 "
            "가장 단순한 구조다. 단일 검색, 검증 없음, 분기 없음 — 직선 파이프라인이라 "
            "관련성이 낮은 청크가 들어와도 그대로 사용한다."
        ),
        metadata={"id": "doc05", "topic": "naive_rag"},
    ),
    Document(
        page_content=(
            "Advanced RAG 는 검색 전·후를 최적화한다. 사전 처리에는 의미 단위 청킹, 쿼리 재작성, "
            "Multi-Query, HyDE 가, 사후 처리에는 Cross-Encoder 리랭킹과 컨텍스트 압축이 있다. "
            "여전히 직선 파이프라인이라는 한계는 남는다."
        ),
        metadata={"id": "doc06", "topic": "advanced_rag"},
    ),
    Document(
        page_content=(
            "Self-RAG 는 모델이 생성 도중 특수한 반성 토큰(Retrieve / IsRelevant / IsSupported / IsUseful)을 "
            "출력하여 자기 행동을 통제한다. 실무에서는 파인튜닝 대신 각 판단을 별도 구조화 출력 호출로 분리해 "
            "LangGraph 노드로 구현하는 방식이 일반적이다."
        ),
        metadata={"id": "doc07", "topic": "self_rag"},
    ),
    Document(
        page_content=(
            "Corrective RAG(CRAG) 는 벡터 검색 결과의 신뢰도를 경량 평가기로 매긴 뒤 세 갈래로 분기한다. "
            "Correct 면 지식 정제, Incorrect 면 웹 검색으로 폴백, Ambiguous 면 둘을 결합한다. "
            "CRAG 의 실무 가치는 사내 문서에 답이 없을 때 외부 최신 정보로 대체하는 안전망이다."
        ),
        metadata={"id": "doc08", "topic": "crag"},
    ),
    Document(
        page_content=(
            "Adaptive RAG 는 질문 복잡도를 먼저 분류해 그에 맞는 최소한의 경로를 선택한다. "
            "단순 질문은 LLM 직접 답, 중간은 단일 검색, 복잡은 분해와 반복 검색을 거친다. "
            "라우팅이 핵심이며 비용·지연 최적화에 강하다."
        ),
        metadata={"id": "doc09", "topic": "adaptive_rag"},
    ),
    Document(
        page_content=(
            "LangGraph 는 LLM 워크플로우를 상태 머신으로 표현하는 라이브러리다. StateGraph 에 노드를 등록하고, "
            "조건부 엣지(conditional edge)로 분기를, add_edge 로 순환(cycle)을 만들 수 있어 "
            "자기교정형 RAG, ReAct 에이전트, 멀티 에이전트 supervisor 패턴을 모두 표현할 수 있다."
        ),
        metadata={"id": "doc10", "topic": "langgraph"},
    ),
]


def get_vectorstore(docs=None):
    """매 호출마다 새 인메모리 Chroma 컬렉션 생성."""
    from langchain_chroma import Chroma
    return Chroma.from_documents(
        documents=list(docs) if docs else SAMPLE_DOCS,
        embedding=get_embeddings(),
        collection_name="agentic_rag_demo",
    )


# ===========================================================================
# 3) 웹 검색 (DuckDuckGo — Tavily 키 없이도 동작)
# ===========================================================================
def web_search_fn(query: str, k: int = 3) -> str:
    """DuckDuckGo 검색 결과 합쳐 한 덩어리의 문서로 반환."""
    try:
        from ddgs import DDGS
    except ImportError:
        from duckduckgo_search import DDGS

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=k))
    except Exception as e:
        return f"[WEB_SEARCH_ERROR] {type(e).__name__}: {e}"

    if not results:
        return "[WEB_SEARCH] 결과 없음"

    return "\n\n".join(
        f"- {r.get('title', '?')}: {r.get('body') or r.get('snippet') or '...'}"
        for r in results
    )


# ===========================================================================
# 4) Neo4j 연결 (supp_04 GraphRAG 모듈용)
# ===========================================================================
def get_neo4j_graph(refresh_schema: bool = True):
    """Neo4jGraph 반환. env 미설정이면 None."""
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    pw = os.getenv("NEO4J_PASSWORD")
    if not (uri and user and pw):
        return None
    from langchain_neo4j import Neo4jGraph
    g = Neo4jGraph(url=uri, username=user, password=pw)
    if refresh_schema:
        try:
            g.refresh_schema()
        except Exception:
            pass
    return g


def reset_neo4j(graph) -> None:
    """그래프 전체 삭제 (실습 재현용)."""
    graph.query("MATCH (n) DETACH DELETE n")


# ===========================================================================
# 5) 출력 헬퍼
# ===========================================================================
def banner(title: str) -> None:
    print("\n" + "=" * 70)
    print(f"📌 {title}")
    print("=" * 70)


def llm_unavailable() -> None:
    print("\n" + "─" * 70)
    print("⚠️  LLM 호출이 필요합니다.")
    print("    OPENROUTER_API_KEY 가 .env 에 없습니다. 스킵합니다.")
    print("─" * 70)
