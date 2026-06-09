"""
05_reflection_and_rewrite.py — Self-Reflection + Query Rewriting

(1) 충실성 검사: 답변이 검색 문서에 근거하는가? (환각 여부)
(2) 유용성 검사: 답변이 질문에 실제로 답하는가?
(3) 쿼리 재작성: 검색에 더 적합하도록 질문을 다듬는다.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from _common import get_llm, binary_yesno, banner, llm_unavailable


HALLUCINATION_SYSTEM = (
    "너는 답변이 주어진 문서에 근거하는지 평가한다. "
    "답변 안의 사실이 문서로부터 도출 가능하면 yes, 지어낸 것이면 no."
)
ANSWER_SYSTEM = "답변이 사용자 질문의 의도를 만족하면 yes, 아니면 no."

REWRITE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "주어진 질문을 벡터 검색에 더 적합하도록 한 줄로 재작성하라. "
     "숨은 의미를 드러내고 핵심 키워드를 명확히 하라. "
     "결과만 출력 (설명 X)."),
    ("human", "원본 질문: {question}"),
])


def main() -> None:
    llm = get_llm()
    if llm is None:
        llm_unavailable()
        return

    question_rewriter = REWRITE_PROMPT | llm | StrOutputParser()

    docs = (
        "LLM 에이전트의 메모리는 단기 메모리(컨텍스트 윈도우)와 "
        "장기 메모리(벡터DB 검색)로 나뉜다."
    )
    question = "에이전트 메모리에는 어떤 종류가 있나?"

    grounded_answer = "에이전트 메모리는 단기 메모리와 장기 메모리로 나뉜다."
    hallucinated_answer = "에이전트 메모리는 RAM 16GB 와 SSD 1TB 로 구성된다."

    banner("Reflection #1 — 충실성 (groundedness)")
    for label, ans in [("근거 있음", grounded_answer), ("환각", hallucinated_answer)]:
        score = binary_yesno(
            llm, HALLUCINATION_SYSTEM,
            f"문서:\n{docs}\n\n답변:\n{ans}",
        )
        print(f"  [{label:>6}]  '{ans}' → 근거={score}")

    banner("Reflection #2 — 유용성 (usefulness)")
    irrelevant_answer = "오늘 날씨가 좋다."
    for label, ans in [("관련 답변", grounded_answer), ("무관 답변", irrelevant_answer)]:
        score = binary_yesno(
            llm, ANSWER_SYSTEM,
            f"질문:\n{question}\n\n답변:\n{ans}",
        )
        print(f"  [{label:>8}]  '{ans}' → 유용={score}")

    banner("Iterative Retrieval — 쿼리 재작성")
    vague = "그거 어떻게 해?"
    better = question_rewriter.invoke({"question": vague})
    print(f"  원본:    {vague!r}")
    print(f"  재작성:  {better.strip()}")


if __name__ == "__main__":
    main()
