"""
rag06_context_compression.py — LLMChainExtractor (컨텍스트 압축)
강의안 5-2 전략 4

검색된 문서 전문을 그대로 LLM 에 넣지 않고, LLM 자신이 질의 관련 부분만 추출해
LLM 입력 토큰을 절약한다. ContextualCompressionRetriever 의 또 다른 활용.

🔑 LLM 호출이 필요. 키 없으면 안내 후 종료.
"""
# ⚠️ 강의안: from langchain.retrievers.document_compressors import LLMChainExtractor
#           from langchain.retrievers import ContextualCompressionRetriever
#   langchain 1.x → langchain_classic
from langchain_classic.retrievers.document_compressors import LLMChainExtractor
from langchain_classic.retrievers import ContextualCompressionRetriever

from _common_rag import (
    SAMPLE_DOCS,
    get_vectorstore,
    get_llm,
    print_results,
    llm_unavailable_notice,
)


def main() -> None:
    llm = get_llm()
    if llm is None:
        llm_unavailable_notice("LLMChainExtractor (LLM이 관련 문장 추출)")
        return

    query = "리랭커가 비싼 이유는?"

    # ── 1) 베이스 retriever (Top-5) ───────────────
    vectorstore = get_vectorstore(SAMPLE_DOCS)
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    # 비교: 압축 전 결과
    raw_docs = vector_retriever.invoke(query)
    print_results("[압축 전] Vector Top-5 (전문)", raw_docs, query)
    print("\n📏 원본 총 길이:", sum(len(d.page_content) for d in raw_docs), "자")

    # ── 2) LLMChainExtractor 로 압축 ─────────────
    compressor = LLMChainExtractor.from_llm(llm)
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=vector_retriever,
    )

    compressed = compression_retriever.invoke(query)
    print_results("[압축 후] 질의 관련 문장만 추출", compressed, query)
    print("\n📏 압축 후 총 길이:", sum(len(d.page_content) for d in compressed), "자")


if __name__ == "__main__":
    main()
