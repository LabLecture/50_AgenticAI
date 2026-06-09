"""
02_query_router.py — Query Routing (질문 라우팅)

LLM 에게 정해진 스키마 (Literal) 로만 분류 결과를 출력하게 강제 — `with_structured_output`.
질문 3종에 대해 vectorstore / web_search / direct_answer 중 어느 경로로 가는지 확인.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from typing import Literal

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from _common import get_llm, structured, banner, llm_unavailable


class RouteQuery(BaseModel):
    """사용자 질문을 가장 적절한 데이터 소스로 라우팅한다."""
    datasource: Literal["vectorstore", "web_search", "direct_answer"] = Field(
        ...,
        description="vectorstore / web_search / direct_answer 중 선택",
    )


ROUTE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "너는 질문 라우터다. 아래 기준으로 단 하나의 라벨만 골라라.\n"
     "- vectorstore: 사내 AI 에이전트·RAG·LangGraph 관련 기술 질문\n"
     "- web_search:  최신 뉴스·시세·실시간 정보 등 외부 최신 정보\n"
     "- direct_answer: 일반 상식·인사·단순 계산\n\n"
     '반드시 다음 JSON 만 출력하라: {{"datasource": "<라벨>"}}'),
    ("human", "{question}"),
])


def main() -> None:
    llm = get_llm()
    if llm is None:
        llm_unavailable()
        return

    router = ROUTE_PROMPT | structured(llm, RouteQuery)

    test_queries = [
        "에이전트 메모리 종류 정리해줘",          # → vectorstore
        "오늘 비트코인 시세 알려줘",                # → web_search
        "안녕! 1 더하기 1 은?",                    # → direct_answer
    ]

    banner("Query Routing — 3종 질문 분류")
    for q in test_queries:
        result = router.invoke({"question": q})
        print(f"  Q: {q!r:<45} → {result.datasource}")


if __name__ == "__main__":
    main()
