"""
07_deepeval_evaluate.py — DeepEval evaluate() 배치 평가

여러 테스트케이스 × 여러 메트릭. RAG end-to-end 평가의 표준 형태.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric

from _common import banner, llm_unavailable
from _judges import deepeval_judge


def main() -> None:
    banner("DeepEval evaluate() — 3 케이스 × 2 메트릭 배치")
    judge = deepeval_judge()
    if judge is None:
        llm_unavailable()
        return

    test_cases = [
        LLMTestCase(
            input="에펠탑은 어디에 있나?",
            actual_output="에펠탑은 프랑스 파리에 있습니다.",
            expected_output="파리.",
            retrieval_context=["에펠탑은 프랑스 파리에 위치한다."],
        ),
        LLMTestCase(
            input="에펠탑은 언제 지어졌나?",
            actual_output="에펠탑은 1889년에 지어졌습니다.",
            expected_output="1889년.",
            retrieval_context=["에펠탑은 1889년 파리 만국박람회를 위해 세워졌다."],
        ),
        LLMTestCase(
            input="에펠탑의 높이는?",
            actual_output="에펠탑은 약 1000m 입니다.",  # 환각
            expected_output="약 330m.",
            retrieval_context=["에펠탑의 높이는 약 330m 이다."],
        ),
    ]

    metrics = [
        AnswerRelevancyMetric(threshold=0.7, model=judge),
        FaithfulnessMetric(threshold=0.7, model=judge),
    ]

    try:
        evaluate(test_cases=test_cases, metrics=metrics)
        # evaluate() 가 자체적으로 콘솔에 요약 출력
    except Exception as e:
        print(f"\n  ⚠ {type(e).__name__}: {str(e)[:300]}")


if __name__ == "__main__":
    main()
