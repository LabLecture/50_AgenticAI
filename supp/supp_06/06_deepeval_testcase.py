"""
06_deepeval_testcase.py — DeepEval LLMTestCase + 단일 메트릭

DeepEval 의 모든 평가는 LLMTestCase 에서 시작.
Ragas 와 필드 이름이 다르다 (input / actual_output / retrieval_context / expected_output).
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric

from _common import banner, llm_unavailable
from _judges import deepeval_judge


def main() -> None:
    banner("DeepEval LLMTestCase — 필드 매핑 + Faithfulness")
    judge = deepeval_judge()
    if judge is None:
        llm_unavailable()
        return

    test_case = LLMTestCase(
        input="에펠탑은 어디에 있나?",
        actual_output="에펠탑은 프랑스 파리에 있습니다.",
        expected_output="에펠탑은 파리에 있습니다.",
        retrieval_context=["에펠탑은 프랑스 파리에 위치한다."],
    )

    print("\n  📋 LLMTestCase 4 필드 (Ragas 와 이름이 다름!):")
    print(f"    input              ← Ragas user_input")
    print(f"    actual_output      ← Ragas response")
    print(f"    expected_output    ← Ragas reference")
    print(f"    retrieval_context  ← Ragas retrieved_contexts")

    metric = FaithfulnessMetric(threshold=0.7, model=judge)
    try:
        metric.measure(test_case)
        print(f"\n  📊 Faithfulness")
        print(f"    score    = {metric.score}")
        print(f"    reason   = {metric.reason[:200] if metric.reason else '-'}")
        print(f"    passed   = {metric.is_successful()}")
    except Exception as e:
        print(f"\n  ⚠ {type(e).__name__}: {str(e)[:200]}")


if __name__ == "__main__":
    main()
