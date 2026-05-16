"""
rag04_reranking_cohere.py — Cohere Reranker API + ContextualCompressionRetriever
강의안 5-2 전략 2 (유료, 다국어 강세)

ContextualCompressionRetriever 패턴:
    base_retriever 가 1차로 가져온 문서를 base_compressor (= 리랭커) 가 추려서 반환.
    리랭커가 문서를 "압축(필터)" 하는 관점.

🔑 COHERE_API_KEY 환경변수가 필요. 없으면 안내 메시지 출력 후 종료.
"""
import os

from langchain_community.retrievers import BM25Retriever

# ⚠️ 강의안: from langchain.retrievers import EnsembleRetriever, ContextualCompressionRetriever
#   langchain 1.x → langchain_classic
from langchain_classic.retrievers import EnsembleRetriever, ContextualCompressionRetriever

from _common_rag import SAMPLE_DOCS, get_vectorstore, print_results


def main() -> None:
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        print("─" * 70)
        print("⚠️  COHERE_API_KEY 환경변수가 설정되어 있지 않습니다.")
        print("    유료 리랭커이므로 키가 필수입니다. https://dashboard.cohere.com 에서 발급.")
        print("    예: $env:COHERE_API_KEY = '...'")
        print("    (무료 대안은 rag03_reranking_local.py 참고)")
        print("─" * 70)
        return

    query = "다국어 리랭킹 API 가 필요한 경우?"

    # ── 1) Hybrid 1차 검색 (Top-10 정도 넉넉히) ──────
    bm25 = BM25Retriever.from_documents(SAMPLE_DOCS)
    bm25.k = 10
    vectorstore = get_vectorstore(SAMPLE_DOCS)
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
    ensemble = EnsembleRetriever(
        retrievers=[bm25, vector_retriever],
        weights=[0.4, 0.6],
    )
    print_results("[1차 검색] Hybrid Top-10", ensemble.invoke(query), query)

    # ── 2) Cohere Reranker ───────────────────────────
    from langchain_cohere import CohereRerank

    reranker = CohereRerank(
        cohere_api_key=api_key,
        model="rerank-multilingual-v3.0",
        top_n=5,
    )
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=reranker,
        base_retriever=ensemble,
    )

    final_docs = compression_retriever.invoke(query)
    print_results("[Cohere 재정렬 후] Top-5", final_docs, query)


if __name__ == "__main__":
    main()
