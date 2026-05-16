"""
rag01_baseline.py — 기본 RAG (Vector Search 단독)
강의안 5-2 도입부 — 비교 기준점

파이프라인:
    질의 → Embedding 검색 → Top-K → (LLM 생성)
"""
from _common_rag import (
    SAMPLE_DOCS,
    get_vectorstore,
    get_llm,
    print_results,
    llm_unavailable_notice,
)


def main() -> None:
    query = "키워드와 의미를 동시에 잘 잡는 검색 방법은?"

    # 1) 벡터 스토어 + 단순 retriever
    vectorstore = get_vectorstore(SAMPLE_DOCS)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    # 2) 검색
    docs = retriever.invoke(query)
    print_results("[Baseline] 순수 Vector Search Top-5", docs, query)

    # 3) LLM 답변 생성 (선택)
    llm = get_llm()
    if llm is None:
        llm_unavailable_notice("최종 답변 생성")
        return

    context = "\n\n".join(f"[{d.metadata['id']}] {d.page_content}" for d in docs)
    prompt = (
        "다음 문서들을 참고하여 질문에 한국어로 간결히 답하라.\n\n"
        f"=== 문서 ===\n{context}\n\n"
        f"=== 질문 ===\n{query}\n"
    )
    response = llm.invoke(prompt)
    print("\n📝 LLM 답변")
    print("-" * 70)
    print(response.content)


if __name__ == "__main__":
    main()
