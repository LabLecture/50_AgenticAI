"""
04_retrieval_grader.py — Retrieval Grading (검색 문서 채점)

벡터 검색으로 top-k 를 가져온 뒤, 각 문서를 LLM 으로 yes/no 채점.
임베딩 유사도 점수와는 별개로 "의미상 정말 답에 도움 되는가" 를 한 번 더 거른다.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from _common import get_llm, binary_yesno, get_vectorstore, SAMPLE_DOCS, banner, llm_unavailable


GRADE_SYSTEM = (
    "너는 검색된 문서의 관련성을 평가하는 채점자다. "
    "엄격할 필요는 없다 — 문서에 질문과 관련된 키워드나 의미가 있으면 yes."
)


def main() -> None:
    llm = get_llm()
    if llm is None:
        llm_unavailable()
        return

    vs = get_vectorstore(SAMPLE_DOCS)
    retriever = vs.as_retriever(search_kwargs={"k": 5})

    question = "Self-RAG 의 반성 토큰은 어떤 종류가 있나?"
    docs = retriever.invoke(question)

    banner(f"Retrieval Grading — query: {question!r}")
    kept = []
    for d in docs:
        doc_id = d.metadata.get("id")
        topic = d.metadata.get("topic")
        score = binary_yesno(
            llm,
            GRADE_SYSTEM,
            f"검색된 문서:\n\n{d.page_content}\n\n사용자 질문: {question}",
        )
        flag = "✅ keep" if score == "yes" else "❌ drop"
        print(f"  {flag} [{doc_id} / {topic}]  {d.page_content[:60]}…")
        if score == "yes":
            kept.append(d)

    print(f"\n  → 통과 {len(kept)}/{len(docs)} 개 (관련 없는 문서는 LLM 컨텍스트에서 제외됨)")


if __name__ == "__main__":
    main()
