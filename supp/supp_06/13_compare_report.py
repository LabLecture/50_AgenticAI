"""
13_compare_report.py — 12 의 결과를 DataFrame 으로 합쳐 요약 표 출력

실제로는 12 의 reports 를 그대로 import 해 쓸 수도 있지만, 본 데모는
*요약 표 작성 패턴*만 보여주고 가짜 점수로 매트릭스 구성 예시를 만든다.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import pandas as pd

from _common import banner


# 실제 12_run_comparison.py 실행 결과를 수동으로 정리한 예시 표.
# 강의에선 12 의 reports 를 받아 같은 식으로 정리한다.
DEMO_RESULTS = {
    "vector":  {"Faithfulness": 0.85, "ResponseRelevancy": 0.82, "ContextRecall": 0.70},
    "agentic": {"Faithfulness": 0.92, "ResponseRelevancy": 0.88, "ContextRecall": 0.75},
    "graph":   {"Faithfulness": 0.88, "ResponseRelevancy": 0.84, "ContextRecall": 0.95},  # 관계형 강점
}


def main() -> None:
    banner("비교 리포트 — 시스템 × 지표 표 + 해석")

    df = pd.DataFrame(DEMO_RESULTS).T
    df.index.name = "system"
    print("\n📊 (데모) 시스템 × 지표")
    print(df.to_string())

    # 최고 점수 색칠 (단순 출력)
    print("\n🏆 지표별 최고 시스템:")
    for col in df.columns:
        winner = df[col].idxmax()
        print(f"  {col:<20}: {winner}  (score={df.loc[winner, col]:.3f})")

    print("\n💡 해석 패턴 (기대값)")
    print("  - Faithfulness 가 Agentic 에서 가장 높음 → 채점/성찰의 환각 감소 효과")
    print("  - ContextRecall 이 Graph 에서 가장 높음 → 관계형 질의의 누락 보완")
    print("  - 그러나 비용/지연도 함께 봐야 — single number 에 휘둘리지 말 것")


if __name__ == "__main__":
    main()
