"""
03_query_decomposition.py — Query Decomposition (질문 분해)

복합 질문을 독립 검색 가능한 하위 질문 N 개로 분해.
단순 질문이면 원본 1개만 반환.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from typing import List

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from _common import get_llm, structured, banner, llm_unavailable


class SubQuestions(BaseModel):
    """복합 질문을 독립적으로 검색 가능한 하위 질문들로 분해."""
    sub_questions: List[str] = Field(
        ...,
        description="각 하위 질문은 단독으로 벡터 검색 가능한 완결된 문장.",
    )


DECOMPOSE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "복잡한 질문을 2~4 개의 독립적인 하위 질문으로 분해하라. "
     "단순 질문이면 원본 질문 하나만 반환하라. "
     "출력은 한국어로.\n\n"
     '반드시 다음 JSON 만 출력하라: {{"sub_questions": ["...", "..."]}}'),
    ("human", "{question}"),
])


def main() -> None:
    llm = get_llm()
    if llm is None:
        llm_unavailable()
        return

    planner = DECOMPOSE_PROMPT | structured(llm, SubQuestions)

    cases = [
        # 1) 복합 — 분해 기대
        "Self-RAG 와 CRAG 의 동작 원리 차이와, 각각이 강조하는 컴포넌트는?",
        # 2) 단순 — 그대로 1개 기대
        "LangGraph 는 무엇인가?",
    ]

    banner("Query Decomposition — 복합 vs 단순 질문")
    for q in cases:
        result = planner.invoke({"question": q})
        print(f"\n  ▶ 원본: {q}")
        for i, sub in enumerate(result.sub_questions, 1):
            print(f"      {i}. {sub}")


if __name__ == "__main__":
    main()
