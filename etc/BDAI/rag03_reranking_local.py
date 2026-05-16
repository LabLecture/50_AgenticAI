"""
rag03_reranking_local.py — 로컬 CrossEncoder 리랭킹
강의안 5-2 전략 2 (무료 대안)

1차로 더 많이(예: Top-10) 가져온 뒤, sentence-transformers CrossEncoder 가
질의-문서 쌍의 관련성 점수를 직접 계산해서 Top-K 로 재정렬한다.

⚠️ 모델 `cross-encoder/ms-marco-MiniLM-L-6-v2` 는 영어 학습 비중이 높다.
   한국어에 더 강한 대안: `Dongjin-kr/ko-reranker`, `BAAI/bge-reranker-v2-m3`
"""
from sentence_transformers import CrossEncoder

from _common_rag import SAMPLE_DOCS, get_vectorstore, print_results


def main() -> None:
    query = "검색된 문서 순위를 LLM 직전에 다시 매기는 방법은?"

    # ── 1) 1차 검색은 넉넉히 (Top-10) ─────────────────
    vectorstore = get_vectorstore(SAMPLE_DOCS)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
    candidates = retriever.invoke(query)
    print_results("[1차 검색] Vector Top-10 (재정렬 전)", candidates, query)

    # ── 2) CrossEncoder 로 점수 계산 ───────────────────
    print("\n⏳ CrossEncoder 모델 로딩 (최초 실행 시 다운로드, ~90MB)...")
    model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    pairs = [(query, d.page_content) for d in candidates]
    scores = model.predict(pairs)

    reranked = sorted(zip(scores, candidates), key=lambda x: float(x[0]), reverse=True)
    top_docs = [d for _, d in reranked[:5]]

    # ── 3) 재정렬 결과 ───────────────────────────────
    print_results("[재정렬 후] CrossEncoder Top-5", top_docs, query)

    print("\n📊 점수 비교 (재정렬 후)")
    print("-" * 70)
    for score, doc in reranked[:5]:
        print(f"  {float(score):+.4f}  [{doc.metadata['id']}] {doc.page_content[:60]}...")


if __name__ == "__main__":
    main()
