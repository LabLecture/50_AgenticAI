"""
12_run_comparison.py — ★ 클라이맥스: 3 RAG 시스템을 같은 테스트셋·같은 지표로 비교

흐름:
  1) 테스트 질문 N 개 정의 (또는 05 에서 합성된 셋 로드)
  2) 각 시스템에 질문을 던져 (answer, contexts) 수집
  3) Ragas 메트릭으로 평가
  4) 시스템 × 지표 표로 정리
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
import importlib

from ragas import SingleTurnSample, EvaluationDataset, evaluate
from ragas.metrics import Faithfulness, ResponseRelevancy, LLMContextRecall

from _common import banner, llm_unavailable
from _judges import ragas_judge, ragas_embeddings

# 11 의 SYSTEMS dict 사용
m11 = importlib.import_module("11_system_adapters")
SYSTEMS = m11.SYSTEMS


TEST_SET = [
    {
        "question": "에이전트 메모리에는 어떤 종류가 있나?",
        "reference": "에이전트 메모리는 단기·장기·감각 세 종류로 나뉜다.",
    },
    {
        "question": "CRAG 는 검색 결과를 어떻게 다루나?",
        "reference": "CRAG 는 신뢰도 평가 후 Correct/Incorrect/Ambiguous 로 분기하며, "
                     "낮으면 웹 검색으로 폴백한다.",
    },
    {
        "question": "LangGraph 의 순환은 어떻게 표현하나?",
        "reference": "LangGraph 는 add_edge / add_conditional_edges 로 노드 간 cycle 을 만들 수 있다.",
    },
]


def main() -> None:
    banner("★ 3 RAG 비교 — 같은 질문, 같은 지표")
    judge = ragas_judge()
    if judge is None:
        llm_unavailable()
        return

    metrics = [
        Faithfulness(llm=judge),
        ResponseRelevancy(llm=judge, embeddings=ragas_embeddings()),
        LLMContextRecall(llm=judge),
    ]

    # ─── Step 1: 시스템별 (answer, contexts) 수집 ───
    print(f"\n📥 Step 1: 각 시스템에 {len(TEST_SET)} 질문 실행")
    reports = {}
    for name, fn in SYSTEMS.items():
        print(f"\n  ── {name} ──")
        samples = []
        for item in TEST_SET:
            q, ref = item["question"], item["reference"]
            try:
                ans, ctxs = fn(q)
                if not ctxs:
                    ctxs = ["(no contexts)"]   # Ragas 가 빈 리스트 거부할 수 있어 placeholder
                samples.append(SingleTurnSample(
                    user_input=q, response=ans,
                    retrieved_contexts=ctxs, reference=ref,
                ))
                print(f"    ✓ {q[:40]}…  ans={ans.strip()[:60]}…")
            except Exception as e:
                print(f"    ✗ {q[:40]}…  {type(e).__name__}: {str(e)[:60]}")

        if not samples:
            print(f"    (시스템 {name} 수집 실패 — 스킵)")
            continue

        # ─── Step 2: 시스템별 Ragas 평가 ───
        print(f"\n  📊 Ragas 평가 중…")
        try:
            reports[name] = evaluate(
                dataset=EvaluationDataset(samples=samples),
                metrics=metrics,
            )
        except Exception as e:
            print(f"    ⚠ 평가 실패: {type(e).__name__}: {str(e)[:120]}")

    # ─── Step 3: 비교 표 ───
    print("\n\n" + "═" * 70)
    print("📊 시스템 × 지표 비교")
    print("═" * 70)
    for name, rep in reports.items():
        print(f"\n  [{name}]")
        print(f"    {rep}")


if __name__ == "__main__":
    main()
