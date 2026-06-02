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

    # ── 5) [심화] BM25 vs Vector blind spot — 강약점이 한 번에 드러나는 시나리오 ──
    # 위의 단일 query 만으로는 두 방식이 거의 비슷해 보인다.
    # 아래 두 시나리오는 각각 한쪽의 약점을 의도적으로 자극해 차이를 드러낸다.
    print("\n" + "═" * 70)
    print("📚 [심화] BM25 vs Vector blind spot — 정답 문서를 어느 쪽이 더 위로 잡는가")
    print("═" * 70)

    def rank_of(doc_id: str, results) -> int | None:
        """검색 결과에서 특정 doc_id 의 순위(1-based). 없으면 None."""
        for i, d in enumerate(results, 1):
            if d.metadata.get("id") == doc_id:
                return i
        return None

    hybrid = EnsembleRetriever(
        retrievers=[bm25, vector_retriever], weights=[0.5, 0.5]
    )

    scenarios = [
        {
            # 정답 doc02 (BM25 설명) 엔 'BM25' 라는 정확 키워드가 있음.
            # 반면 Vector 는 '한국어' 라는 토큰에 끌려 다국어 모델 얘기인 doc05(Cohere) 로 빠짐.
            "query": "키워드 검색의 한국어 처리",
            "target": "doc02",
            "expect": "BM25 우위 — 정답엔 'BM25' 가 직접 등장. '한국어' 가 Vector 를 doc05(Cohere 다국어) 로 끌어감",
        },
        {
            # 정답 doc04 (Cross-Encoder 리랭커) 엔 query 의 단어가 거의 안 나옴.
            # BM25 는 '검색/결과/모델' 같은 흔한 단어로 doc04 를 놓치고, Vector 는 의미로 잡아냄.
            "query": "검색 결과를 좁은 후보에서 한 번 더 정렬하는 모델",
            "target": "doc04",
            "expect": "Vector 우위 — 정답 doc04 의 단어가 query 와 겹치지 않음 (BM25 는 Top-5 밖)",
        },
    ]

    for s in scenarios:
        bm_rank = rank_of(s["target"], bm25.invoke(s["query"]))
        vc_rank = rank_of(s["target"], vector_retriever.invoke(s["query"]))
        hy_rank = rank_of(s["target"], hybrid.invoke(s["query"]))

        def fmt(r):
            return f"{r:>3}" if r is not None else "  ✗"  # 검색 결과에 없으면 ✗

        print(f"\n🎯 query  : {s['query']!r}")
        print(f"   기대   : {s['expect']}")
        print(f"   정답   : {s['target']}")
        print(f"   ── 정답 문서의 순위 (낮을수록 좋음, ✗ = Top-5 안에 없음) ──")
        print(f"     BM25 단독        : {fmt(bm_rank)}")
        print(f"     Vector 단독      : {fmt(vc_rank)}")
        print(f"     Hybrid 0.5/0.5   : {fmt(hy_rank)}")

    print("\n" + "─" * 70)
    print("💡 해석: Hybrid 의 강점 = '두 방식 중 잘 잡은 쪽 결과를 따라간다'")
    print("    한쪽이 정답을 못 잡아도 다른 쪽이 보완 → 단일 retriever 보다 안전")
    print("─" * 70)


if __name__ == "__main__":
    main()
