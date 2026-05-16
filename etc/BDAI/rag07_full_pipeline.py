"""
rag07_full_pipeline.py — 통합 고도화 RAG 파이프라인
강의안 5-2 마지막 요약

흐름:
    질의
      │
      ├─ MultiQuery (LLM 변형)              ← rag05
      ▼
    Hybrid Search (BM25 + Vector, Top-10)   ← rag02
      │
      ▼
    CrossEncoder Rerank (Top-5)             ← rag03 (로컬)
      │
      ▼
    LLMChainExtractor 압축                   ← rag06
      │
      ▼
    LLM 최종 답변 생성

LLM/Cohere 키가 없을 때:
    - MultiQuery 단계는 키가 있으면 활성, 없으면 원본 질의만 사용
    - Cohere 대신 항상 로컬 CrossEncoder 사용
    - 압축은 LLM 키가 있을 때만 활성
    - 최종 답변은 LLM 키가 있을 때만 생성
"""
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever, ContextualCompressionRetriever
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from langchain_classic.retrievers.document_compressors import LLMChainExtractor
from sentence_transformers import CrossEncoder

from _common_rag import (
    SAMPLE_DOCS,
    get_vectorstore,
    get_llm,
    print_results,
)


def cross_encoder_rerank(query: str, docs, top_k: int = 5):
    if not docs:
        return docs
    model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    pairs = [(query, d.page_content) for d in docs]
    scores = model.predict(pairs)
    return [d for _, d in sorted(zip(scores, docs), key=lambda x: float(x[0]), reverse=True)[:top_k]]


def main() -> None:
    query = "RAG 검색 품질을 종합적으로 올리려면?"
    llm = get_llm()

    # ── 1) Hybrid 베이스 검색기 (Top-10) ─────────
    bm25 = BM25Retriever.from_documents(SAMPLE_DOCS)
    bm25.k = 10
    vectorstore = get_vectorstore(SAMPLE_DOCS)
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
    hybrid = EnsembleRetriever(retrievers=[bm25, vector_retriever], weights=[0.4, 0.6])

    # ── 2) Query 변환 (LLM 있으면) ────────────────
    if llm is not None:
        retriever = MultiQueryRetriever.from_llm(retriever=hybrid, llm=llm)
        print("✅ MultiQueryRetriever 활성")
    else:
        retriever = hybrid
        print("⚠️ LLM 키 없음 → 원본 질의만 사용 (MultiQuery 비활성)")

    initial_docs = retriever.invoke(query)
    print_results("[1단계] Hybrid (+MultiQuery) 검색 결과", initial_docs, query)

    # ── 3) CrossEncoder 리랭크 (항상) ─────────────
    print("\n⏳ CrossEncoder 로딩...")
    reranked = cross_encoder_rerank(query, initial_docs, top_k=5)
    print_results("[2단계] CrossEncoder 리랭크 후 Top-5", reranked, query)

    # ── 4) 컨텍스트 압축 (LLM 있으면) ─────────────
    if llm is not None:
        print("\n⏳ 컨텍스트 압축 중...")
        compressor = LLMChainExtractor.from_llm(llm)
        # ContextualCompressionRetriever 는 retriever 인터페이스를 요구하므로,
        # 이미 가지고 있는 docs 를 직접 압축하도록 compress_documents 호출.
        compressed = list(compressor.compress_documents(reranked, query))
        print_results("[3단계] LLMChainExtractor 압축 후", compressed, query)
        final_context_docs = compressed
    else:
        print("\n⚠️ LLM 키 없음 → 컨텍스트 압축 단계 스킵")
        final_context_docs = reranked

    # ── 5) 최종 답변 생성 ────────────────────────
    if llm is None:
        print("\n⚠️ LLM 키 없음 → 최종 답변 생성 스킵")
        print("   여기까지의 결과만으로도 retrieval 품질 변화는 충분히 확인 가능합니다.")
        return

    context = "\n\n".join(
        f"[{d.metadata.get('id', '?')}] {d.page_content}" for d in final_context_docs
    )
    prompt = (
        "다음 문서들을 참고하여 질문에 한국어로 5문장 이내로 답하라.\n\n"
        f"=== 문서 ===\n{context}\n\n"
        f"=== 질문 ===\n{query}\n"
    )
    answer = llm.invoke(prompt)
    print("\n📝 [최종] LLM 답변")
    print("-" * 70)
    print(answer.content)


if __name__ == "__main__":
    main()
