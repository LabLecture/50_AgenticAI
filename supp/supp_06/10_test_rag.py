"""
10_test_rag.py — DeepEval + pytest 통합 (평가를 단위 테스트로)

실행:
    pytest 10_test_rag.py                   (또는)
    deepeval test run 10_test_rag.py        (deepeval 캐싱/리포트 활용)

CI/CD 게이트로 활용 시 — threshold 미달이면 PR 차단.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import pytest

from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric

from _judges import deepeval_judge


# 골든셋 — 질문 + 기대 답 + 컨텍스트
GOLDEN_CASES = [
    {
        "input": "에펠탑은 어디에 있나?",
        "actual_output": "에펠탑은 파리에 있습니다.",
        "retrieval_context": ["에펠탑은 프랑스 파리에 위치한다."],
    },
    {
        "input": "에펠탑은 언제 지어졌나?",
        "actual_output": "에펠탑은 1889년에 지어졌습니다.",
        "retrieval_context": ["에펠탑은 1889년 만국박람회를 위해 세워졌다."],
    },
]


@pytest.fixture(scope="module")
def judge():
    return deepeval_judge()


@pytest.mark.parametrize("case", GOLDEN_CASES)
def test_rag(case, judge):
    """assert_test 가 threshold 미달이면 raise → pytest FAIL → CI 빌드 실패."""
    if judge is None:
        pytest.skip("OPENROUTER_API_KEY 미설정")

    tc = LLMTestCase(**case)
    assert_test(
        tc,
        metrics=[
            AnswerRelevancyMetric(threshold=0.7, model=judge),
            FaithfulnessMetric(threshold=0.7, model=judge),
        ],
    )
