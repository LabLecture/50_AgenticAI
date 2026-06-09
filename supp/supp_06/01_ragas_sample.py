"""
01_ragas_sample.py — Ragas 의 SingleTurnSample 구조 (LLM 호출 없음)

평가 한 건을 표현하는 핵심 데이터 구조 시연.
필드 이름 (user_input / response / retrieved_contexts / reference) 이 곧 평가 메트릭의 입력.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from ragas import SingleTurnSample
from _common import banner


def main() -> None:
    banner("Ragas SingleTurnSample — 평가 한 건의 4 필드")

    sample = SingleTurnSample(
        user_input="에펠탑은 어디에 있나?",
        response="에펠탑은 파리에 있습니다.",
        retrieved_contexts=["에펠탑은 프랑스 파리에 위치한다."],
        reference="에펠탑은 파리에 있습니다.",
    )

    print("\n  📋 4 가지 필드:")
    print(f"    user_input         : {sample.user_input}")
    print(f"    response           : {sample.response}")
    print(f"    retrieved_contexts : {sample.retrieved_contexts}")
    print(f"    reference          : {sample.reference}")

    print("\n  📊 각 필드가 어떤 메트릭에 쓰이는지:")
    print(f"    Faithfulness         ← response + retrieved_contexts")
    print(f"    ResponseRelevancy    ← user_input + response")
    print(f"    LLMContextPrecision  ← user_input + retrieved_contexts + reference")
    print(f"    LLMContextRecall     ← user_input + retrieved_contexts + reference")


if __name__ == "__main__":
    main()
