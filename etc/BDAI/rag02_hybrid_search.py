"""
rag02_hybrid_search.py — Hybrid Search (BM25 + Vector)
강의안 5-2 전략 1

BM25 (sparse, 키워드) + Vector (dense, 의미) 의 결과를 EnsembleRetriever 로 결합한다.
가중치를 바꿔가며 효과를 비교한다.
"""
from langchain_community.retrievers import BM25Retriever

# ⚠️ 강의안: from langchain.retrievers import EnsembleRetriever
#   langchain 1.x 부터는 langchain_classic 으로 이동했다.
from langchain_classic.retrievers import EnsembleRetriever

from _common_rag import SAMPLE_DOCS, get_vectorstore, print_results


def main() -> None:
    query = "정확한 단어 일치는 잘 되는데 동의어를 못 잡는 검색은?"

    # ── 1) BM25 (sparse) ─────────────────────────────
    bm25 = BM25Retriever.from_documents(SAMPLE_DOCS)
    bm25.k = 5

    # ── 2) Vector (dense) ─────────────────────────────
    vectorstore = get_vectorstore(SAMPLE_DOCS)
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    # ── 3) 단독 결과 비교 ─────────────────────────────
    print_results("[BM25 단독] Top-5", bm25.invoke(query), query)
    print_results("[Vector 단독] Top-5", vector_retriever.invoke(query), query)

    # ── 4) Ensemble (가중치 변경 실험) ────────────────
    for weights in [(0.5, 0.5), (0.4, 0.6), (0.7, 0.3)]:
        ensemble = EnsembleRetriever(
            retrievers=[bm25, vector_retriever],
            weights=list(weights),
        )
        docs = ensemble.invoke(query)
        print_results(
            f"[Hybrid bm25={weights[0]} vector={weights[1]}] Top-{len(docs)}",
            docs,
            query,
        )


if __name__ == "__main__":
    main()
