"""
08_deepeval_geval.py — G-Eval 로 자연어 기준 커스텀 평가

내장 메트릭으로 잡을 수 없는 *도메인 특화 기준* (브랜드 톤, 작업 완수 여부, 면책 문구 등) 을
자연어 criteria 문장으로 정의하면 심판 LLM 이 그 기준으로 채점.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from _common import banner, llm_unavailable
from _judges import deepeval_judge


def main() -> None:
    banner("G-Eval — 자연어 기준 커스텀 평가")
    judge = deepeval_judge()
    if judge is None:
        llm_unavailable()
        return

    # 1) 정확성 (사실 일치)
    correctness = GEval(
        name="Correctness",
        criteria=(
            "실제 출력이 기대 출력과 사실적으로 일치하는지 평가하라. "
            "사소한 표현 차이는 허용하되 사실이 틀리면 낮게 채점하라."
        ),
        evaluation_params=[
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.EXPECTED_OUTPUT,
        ],
        threshold=0.7,
        model=judge,
    )

    # 2) 작업 완수 (의도 충족)
    task_completion = GEval(
        name="TaskCompletion",
        criteria=(
            "응답이 사용자가 요청한 작업을 실제로 완수했는지 평가하라. "
            "단순 사과/지연 답변은 낮게 채점."
        ),
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        threshold=0.75,
        model=judge,
    )

    cases = [
        ("정답 + 완수",
         LLMTestCase(
             input="에펠탑은 어디에 있나?",
             actual_output="에펠탑은 파리에 있습니다.",
             expected_output="파리.",
         )),
        ("사실 오답",
         LLMTestCase(
             input="에펠탑은 어디에 있나?",
             actual_output="에펠탑은 베이징에 있습니다.",
             expected_output="파리.",
         )),
        ("답 회피 (완수 X)",
         LLMTestCase(
             input="에펠탑은 어디에 있나?",
             actual_output="죄송하지만 그 정보를 모릅니다.",
             expected_output="파리.",
         )),
    ]

    for label, tc in cases:
        print(f"\n  [{label}]  actual={tc.actual_output!r}")
        for metric in [correctness, task_completion]:
            try:
                metric.measure(tc)
                print(f"    {metric.__name__:>16}: score={metric.score:.3f}  pass={metric.is_successful()}")
            except Exception as e:
                print(f"    {metric.__name__:>16}: ⚠ {type(e).__name__}: {str(e)[:80]}")


if __name__ == "__main__":
    main()
