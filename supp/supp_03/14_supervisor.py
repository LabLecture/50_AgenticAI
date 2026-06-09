"""
14_supervisor.py — Supervisor agent

역할 분리:
  - Sub-agent (13) = "외부 자원을 다루는 작업자" (검색·채점·웹)
  - Supervisor (이 파일) = "추론 + 조율" 담당
      1) supervisor_route       : 다음에 어느 sub-agent / 자체 기능을 호출할지 결정
      2) supervisor_generate    : 자체 LLM 으로 최종 답변 작성
      3) supervisor_transform   : 자체 LLM 으로 검색어 재작성

10_build_and_run.py 와 비교:
  - generate / transform_query 는 *원래 그래프의 노드* 였으나, 멀티에이전트에선
    supervisor 의 "내장 능력" 으로 격상. sub-agent 호출 사이의 사고(thought) 역할.
  - decide_to_generate / grade_generation 의 분기 로직도 supervisor_route 로 통합.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))    # supp/ → _common.py

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from _common import get_llm

MAX_ITERATIONS = 12   # supervisor 무한 루프 방지 (데모 3 의 web 폴백 + 재채점 여유분 포함)

_llm = None
_rewriter = None
_rag_chain = None


def _init():
    global _llm, _rewriter, _rag_chain
    if _llm is not None:
        return
    _llm = get_llm()

    _rewriter = (
        ChatPromptTemplate.from_messages([
            ("system", "사용자 질문을 외부 검색에 더 적합하도록 한국어 한 줄로 재작성. 결과만 출력."),
            ("human", "원본: {question}"),
        ])
        | _llm | StrOutputParser()
    )

    _rag_chain = (
        ChatPromptTemplate.from_messages([
            ("system",
             "다음 컨텍스트만 근거로 한국어로 3 문장 이내 답변. "
             "컨텍스트에 없는 사실은 추측 금지. 모르면 모른다고 답하라.\n\n{context}"),
            ("human", "{question}"),
        ])
        | _llm | StrOutputParser()
    )


# ─────────────────────────────────────────────────────────────
# Supervisor 의 라우팅 (어느 노드를 다음에 부를지)
# ─────────────────────────────────────────────────────────────
def supervisor_route(state) -> dict:
    """state 의 last_action / documents / web_search_needed 를 보고 next_agent 결정."""
    last = state.get("last_action")
    iters = state.get("iteration", 0) + 1
    web_flag = state.get("web_search_needed")
    has_docs = bool(state.get("documents"))

    # ⚠ 순서 중요:
    #   ① "generate 끝났으면 무조건 종료" 를 가장 먼저 검사
    #      (그래야 안전망이 generate 후에도 또 generate 를 부르는 무한 루프 방지)
    #   ② 그 다음 안전망 (iteration 초과 시 강제 generate)
    #   ③ 마지막에 정상 라우팅
    if last == "generate":
        decision = "done"

    elif iters > MAX_ITERATIONS:
        # 마지막 시도: 자료 부족이라도 답변 생성하고 종료
        decision = "supervisor_generate"

    elif last is None:
        # 첫 진입 → 사내 검색부터
        decision = "retrieve_agent"

    elif last == "retrieve":
        decision = "grade_agent"

    elif last == "grade":
        if has_docs:
            decision = "supervisor_generate"            # 관련 문서 있음 → 답변
        elif web_flag == "Yes":
            decision = "supervisor_transform"           # 웹 검색 전에 검색어 다듬기
        else:
            decision = "supervisor_generate"            # 폴백 (관련은 없는데 yes 도 아님)

    elif last == "transform":
        decision = "web_search_agent"

    elif last == "web_search":
        decision = "grade_agent"

    else:
        decision = "done"

    print(f"  🧭 [supervisor_route] iter={iters} last={last!s:<10} → next={decision}")
    return {"next_agent": decision, "iteration": iters}


def supervisor_route_edge(state) -> str:
    """conditional edges 매핑용 (state.next_agent 그대로 반환)."""
    return state["next_agent"]


# ─────────────────────────────────────────────────────────────
# Supervisor 자체 기능 1: 답변 생성
# ─────────────────────────────────────────────────────────────
def supervisor_generate(state) -> dict:
    """🧠 [supervisor] 컨텍스트 기반 최종 답변 작성."""
    _init()
    print("  🧠 [supervisor] generate — 답변 작성")
    ctx_docs = state.get("documents", []) or ["(관련 문서 없음 — 일반 지식으로 답하지 말 것)"]
    answer = _rag_chain.invoke({
        "context": "\n\n".join(ctx_docs),
        "question": state["question"],
    })
    return {"answer": answer, "last_action": "generate"}


# ─────────────────────────────────────────────────────────────
# Supervisor 자체 기능 2: 검색어 재작성
# ─────────────────────────────────────────────────────────────
def supervisor_transform(state) -> dict:
    """🧠 [supervisor] 외부 검색 전 검색어 재작성."""
    _init()
    print("  🧠 [supervisor] transform_query — 검색어 재작성")
    new_q = _rewriter.invoke({"question": state["question"]}).strip()
    print(f"     → {new_q}")
    return {"question": new_q, "last_action": "transform"}


if __name__ == "__main__":
    print("14_supervisor.py — supervisor 노드 함수 시그니처")
    print("  - supervisor_route       : (state) → {'next_agent', 'iteration'}")
    print("  - supervisor_generate    : (state) → {'answer', 'last_action'}")
    print("  - supervisor_transform   : (state) → {'question', 'last_action'}")
    print(f"\n  MAX_ITERATIONS = {MAX_ITERATIONS}  (무한 루프 방지)")
