"""
05_ragas_testset.py — Ragas TestsetGenerator 로 합성 테스트셋 생성 (개념 시연)

문서 더미 → LLM 으로 (질문, 정답, 컨텍스트) 자동 생성.

⚠️ TestsetGenerator 는 LLM 호출이 *매우* 많고 (문서당 수십 회) free 모델에선 429 가 잦음.
이 스크립트는 small testset_size=3 으로 시연만 하고, 실패하면 graceful skip.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from _common import banner, llm_unavailable, SAMPLE_DOCS
from _judges import ragas_judge, ragas_embeddings


def main() -> None:
    banner("Ragas TestsetGenerator — 합성 테스트셋 생성")
    judge = ragas_judge()
    if judge is None:
        llm_unavailable()
        return

    try:
        from ragas.testset import TestsetGenerator

        gen = TestsetGenerator(llm=judge, embedding_model=ragas_embeddings())

        # supp_03 의 SAMPLE_DOCS (10 개 한국어 RAG 문서) 를 입력으로 사용
        print(f"  입력 문서: {len(SAMPLE_DOCS)} 개 (supp 의 SAMPLE_DOCS 재사용)")

        testset = gen.generate_with_langchain_docs(
            SAMPLE_DOCS,
            testset_size=3,                # free 모델 호환 위해 작게
        )
        df = testset.to_pandas()
        print(f"\n  ✅ 생성된 테스트셋 ({len(df)} 개)")
        print(df[["user_input", "reference"]].to_string(index=False, max_colwidth=80))
        print(f"\n  → 이 테스트셋을 04_ragas_evaluate.py 의 입력으로 그대로 사용 가능")
    except Exception as e:
        print(f"\n  ⚠ TestsetGenerator 실행 실패 ({type(e).__name__})")
        print(f"     {str(e)[:200]}")
        print(f"  → free 모델의 429 또는 그래프 추출 단계 비호환 가능성.")
        print(f"     실무에선 GPT-4o / Claude 같은 강한 심판 LLM 권장.")


if __name__ == "__main__":
    main()
