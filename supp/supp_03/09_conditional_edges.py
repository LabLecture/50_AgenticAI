"""
09_conditional_edges.py — 조건부 엣지 함수 정의

각 함수는 GraphState 를 보고 *다음에 갈 노드 이름* (문자열) 을 반환한다.

⚠ structured output 은 free 모델에서 불안정하므로 binary_yesno helper 사용.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from _common import get_llm, binary_yesno, banner

MAX_RETRIES = 3


# ── 채점 후 분기 ───────────────────────────────────────────────────
def decide_to_generate(state) -> str:
    """채점 통과 문서가 있으면 generate, 없으면 (재시도 가능하면) transform_query."""
    print("--- ASSESS GRADED DOCUMENTS ---")
    if state.get("web_search") == "Yes":
        if state.get("retry_count", 0) >= MAX_RETRIES:
            print("    재시도 상한 도달 → 강제 generate")
            return "generate"
        print("    관련 문서 0 → transform_query 로")
        return "transform_query"
    print("    관련 문서 있음 → generate 로")
    return "generate"


# ── 생성 후 분기 (충실성/유용성 검사) ─────────────────────────────
def grade_generation(state) -> str:
    """충실성(grounded) + 유용성(useful) 검사 후 다음 행동 결정."""
    print("--- CHECK HALLUCINATION & USEFULNESS ---")
    llm = get_llm()

    # (1) 충실성
    hallu = binary_yesno(
        llm,
        "답변이 주어진 문서에 근거하면 yes, 지어냈으면 no.",
        f"문서:\n{chr(10).join(state['documents'])}\n\n답변:\n{state['generation']}",
    )
    if hallu == "no":
        if state.get("retry_count", 0) >= MAX_RETRIES:
            print("    환각 감지 but 상한 도달 → useful 로 종료")
            return "useful"
        print("    환각 감지 → not_supported (재생성)")
        return "not_supported"

    # (2) 유용성
    useful = binary_yesno(
        llm,
        "답변이 사용자 질문의 의도를 만족하면 yes, 아니면 no.",
        f"질문:\n{state['question']}\n\n답변:\n{state['generation']}",
    )
    if useful == "yes":
        print("    useful=yes → END")
        return "useful"
    if state.get("retry_count", 0) >= MAX_RETRIES:
        print("    useful=no but 상한 도달 → useful 로 종료")
        return "useful"
    print("    useful=no → not_useful (쿼리 재작성)")
    return "not_useful"


# ── 단독 실행 ──────────────────────────────────────────────────────
if __name__ == "__main__":
    banner("09_conditional_edges.py — 분기 함수")
    print(f"  - decide_to_generate(state) → 'transform_query' | 'generate'")
    print(f"  - grade_generation(state)   → 'not_supported' | 'useful' | 'not_useful'")
    print(f"  - MAX_RETRIES = {MAX_RETRIES}")
