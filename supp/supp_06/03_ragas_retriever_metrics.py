"""
03_ragas_retriever_metrics.py — Ragas 검색기 지표

- LLMContextPrecisionWithReference: 가져온 컨텍스트 중 정답에 *유용* 한 비율 (노이즈↓)
- LLMContextRecall:                  정답의 각 주장이 컨텍스트에 다 들어 있는지 (누락↓)

같은 reference 에 대해 두 가지 검색 결과 (관련 vs 노이즈 섞임) 를 비교.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import asyncio

from ragas import SingleTurnSample
from ragas.metrics import LLMContextPrecisionWithReference, LLMContextRecall

from _common import banner, llm_unavailable
from _judges import ragas_judge


def main() -> None:
    banner("Ragas — Context Precision / Recall")
    judge = ragas_judge()
    if judge is None:
        llm_unavailable()
        return

    precision = LLMContextPrecisionWithReference(llm=judge)
    recall = LLMContextRecall(llm=judge)

    question = "에펠탑은 어디에 있고 언제 만들어졌나?"
    reference = "에펠탑은 프랑스 파리에 있으며 1889년에 만들어졌다."

    scenarios = [
        ("관련 컨텍스트만",
         ["에펠탑은 프랑스 파리에 위치한다.",
          "에펠탑은 1889년 파리 만국박람회를 위해 세워졌다."]),
        ("관련+노이즈",
         ["에펠탑은 프랑스 파리에 위치한다.",
          "축구공의 표준 둘레는 약 70cm 이다.",
          "에펠탑은 1889년 파리 만국박람회를 위해 세워졌다.",
          "기린은 잎을 먹기 위해 긴 목을 가졌다."]),
        ("관련 부족 (누락)",
         ["에펠탑은 프랑스 파리에 위치한다."]),  # 1889년 정보 빠짐
    ]

    for label, ctxs in scenarios:
        sample = SingleTurnSample(
            user_input=question,
            response="에펠탑은 파리에 있고 1889년에 만들어졌다.",
            retrieved_contexts=ctxs,
            reference=reference,
        )
        p = asyncio.run(precision.single_turn_ascore(sample))
        r = asyncio.run(recall.single_turn_ascore(sample))
        print(f"\n  [{label}]  Precision={p:.3f}  Recall={r:.3f}")
        print(f"    contexts: {len(ctxs)} 개")


if __name__ == "__main__":
    main()
