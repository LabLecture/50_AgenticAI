"""
04_ragas_evaluate.py — Ragas evaluate() 로 여러 샘플·여러 메트릭 배치 평가

실무 표준 형태: EvaluationDataset + 메트릭 리스트 + evaluate() → DataFrame.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from ragas import SingleTurnSample, EvaluationDataset, evaluate
from ragas.metrics import (
    Faithfulness,
    ResponseRelevancy,
    LLMContextPrecisionWithReference,
    LLMContextRecall,
)

from _common import banner, llm_unavailable
from _judges import ragas_judge, ragas_embeddings


SAMPLES = [
    SingleTurnSample(
        user_input="에펠탑은 어디에 있나?",
        response="에펠탑은 프랑스 파리에 있습니다.",
        retrieved_contexts=["에펠탑은 프랑스 파리에 위치한다."],
        reference="에펠탑은 파리에 있다.",
    ),
    SingleTurnSample(
        user_input="에펠탑은 언제 지어졌나?",
        response="에펠탑은 1889년에 지어졌습니다.",
        retrieved_contexts=["에펠탑은 1889년 파리 만국박람회를 위해 세워졌다."],
        reference="에펠탑은 1889년에 지어졌다.",
    ),
    SingleTurnSample(
        user_input="에펠탑의 높이는?",
        response="에펠탑은 약 1000m 높이입니다.",   # 환각
        retrieved_contexts=["에펠탑의 높이는 약 330m 이다."],
        reference="약 330m.",
    ),
]


def main() -> None:
    banner("Ragas evaluate() — 3 샘플 × 4 메트릭 배치 평가")
    judge = ragas_judge()
    if judge is None:
        llm_unavailable()
        return

    dataset = EvaluationDataset(samples=SAMPLES)

    metrics = [
        Faithfulness(llm=judge),
        ResponseRelevancy(llm=judge, embeddings=ragas_embeddings()),
        LLMContextPrecisionWithReference(llm=judge),
        LLMContextRecall(llm=judge),
    ]

    result = evaluate(dataset=dataset, metrics=metrics)

    print("\n📊 메트릭별 평균 점수")
    print(f"  {result}")

    print("\n📋 샘플별 상세 (DataFrame)")
    df = result.to_pandas()
    cols = [c for c in df.columns if c in
            ("user_input", "faithfulness", "answer_relevancy",
             "llm_context_precision_with_reference", "context_recall")]
    print(df[cols].to_string(index=False))


if __name__ == "__main__":
    main()
