"""
02_ragas_single_metric.py — Ragas Faithfulness 단일 측정

답변을 주장으로 분해 → 각 주장이 컨텍스트에 근거하는지 심판 LLM 이 판정 → 비율 점수.

3 가지 (response, retrieved_contexts) 조합으로 점수 차이를 비교:
  - 근거 있는 답  → 점수 높음
  - 추가 정보 포함 → 점수 중간
  - 환각          → 점수 낮음
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import asyncio

from ragas import SingleTurnSample
from ragas.metrics import Faithfulness

from _common import banner, llm_unavailable
from _judges import ragas_judge


def main() -> None:
    banner("Ragas Faithfulness — 답이 컨텍스트에 근거하는가")
    judge = ragas_judge()
    if judge is None:
        llm_unavailable()
        return

    metric = Faithfulness(llm=judge)

    ctx = ["에펠탑은 1889년 파리 만국박람회를 위해 세워졌고 높이는 약 330m 이다."]
    cases = [
        ("근거 있음",
         "에펠탑은 파리에 있으며 1889년에 만들어졌습니다.",
         "→ 모든 주장이 컨텍스트에 근거"),
        ("추가 환각",
         "에펠탑은 파리에 있으며 매년 700만 명이 방문합니다.",
         "→ '700만 명 방문' 은 컨텍스트에 없음 (환각)"),
        ("완전 환각",
         "에펠탑은 베이징에 있고 50m 높이의 목조 건축물입니다.",
         "→ 모든 주장이 컨텍스트와 모순"),
    ]

    for label, response, note in cases:
        sample = SingleTurnSample(
            user_input="에펠탑은 어디에 있고 언제 만들어졌나?",
            response=response,
            retrieved_contexts=ctx,
        )
        score = asyncio.run(metric.single_turn_ascore(sample))
        print(f"\n  [{label}]  Faithfulness={score:.3f}")
        print(f"    response: {response}")
        print(f"    {note}")


if __name__ == "__main__":
    main()
