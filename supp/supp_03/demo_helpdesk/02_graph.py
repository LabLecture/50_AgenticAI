"""
02_graph.py — 사내 헬프데스크 에이전트 그래프 (supp_03 종합 데모 A-1).

supp_03 단편 실습의 컴포넌트들이 한 그래프에 모인다:
  · 02_query_router      → router 노드 (db / doc / hybrid 3분기)
  · 03_decomposition     → hybrid 노드 내부 (문서질문 + DB질문 분해)
  · 04_retrieval_grader  → grade 노드
  · 05_crag(재작성 루프)  → rewrite 노드 (최대 2회) + no_evidence 정직 응답
  · 06~10 State/엣지 골격 → 그대로 확장

여기에 실전 요소 두 가지가 추가된다:
  · DB 조회 (PostgreSQL) — 개인 연차/경비는 문서가 아니라 DB에 있다
  · 멀티턴 슬롯필링 — 사번을 모르면 되묻고, 받으면 원래 질문을 이어서 처리
"""
import re
from datetime import date
from typing import List, TypedDict

from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from _demo_common import (
    get_llm, get_rules_vectorstore, get_conn, structured, binary_yesno,
)

TODAY = date(2026, 6, 13)   # 데모 재현성을 위해 고정 (실서비스는 date.today())


# ===========================================================================
# State
# ===========================================================================
class HelpdeskState(TypedDict, total=False):
    question: str          # 현재 처리 중인 질문 (재작성될 수 있음)
    original_question: str
    route: str             # db / doc / hybrid
    slots: dict            # {"emp_id": "E1003"} — 멀티턴 누적
    awaiting: str          # 직전 턴에 되물은 슬롯 이름 ("" = 없음)
    pending_question: str  # 슬롯이 채워지면 이어서 처리할 질문
    pending_route: str
    docs: List
    grade_ok: bool
    rewrite_count: int
    answer: str
    trace: List[str]       # 데모용: 어떤 노드를 지났는지


def _t(state: HelpdeskState, msg: str) -> List[str]:
    return state.get("trace", []) + [msg]


EMP_RE = re.compile(r"\b(E?)(\d{4})\b", re.I)


# ===========================================================================
# 노드 1 — ingest: 슬롯필링 응답인지 먼저 확인
# ===========================================================================
def ingest(state: HelpdeskState) -> dict:
    q = state["question"].strip()
    out: dict = {
        "original_question": q,
        "docs": [], "grade_ok": False, "rewrite_count": 0, "answer": "",
        "trace": _t(state, f"ingest: {q!r}"),
    }
    # 직전 턴에 사번을 물었고, 이번 발화가 사번이면 → 슬롯 채우고 원래 질문 복원
    if state.get("awaiting") == "emp_id":
        m = EMP_RE.search(q)
        if m:
            emp_id = "E" + m.group(2)
            out["slots"] = {**state.get("slots", {}), "emp_id": emp_id}
            out["question"] = state["pending_question"]
            out["original_question"] = state["pending_question"]
            out["route"] = state["pending_route"]
            out["awaiting"] = ""
            out["trace"].append(f"slot_fill: emp_id={emp_id} → 원래 질문 재개")
            return out
    out["awaiting"] = ""
    return out


# ===========================================================================
# 노드 2 — router: db / doc / hybrid 3분기  (supp_03/02 재사용)
# ===========================================================================
class RouteDecision(BaseModel):
    route: str = Field(description="'db' | 'doc' | 'hybrid' 중 하나")


ROUTER_SYS = """너는 사내 헬프데스크의 질문 라우터다. 질문을 분류해 JSON 으로만 답하라.
- "db": 특정 직원 개인의 현황·수치 (내 연차 며칠, 내 경비 정산 상태 등)
- "doc": 회사 규정·제도·절차에 대한 일반 질문 (이월 규정, 재택근무 규칙 등)
- "hybrid": 개인 현황과 규정을 모두 알아야 답할 수 있는 질문
  (예: "작년에 이월한 연차도 올해 쓸 수 있어요?" → 내 이월일수(DB) + 이월 사용기한(규정))
출력: {"route": "db" | "doc" | "hybrid"}"""


def router(state: HelpdeskState) -> dict:
    llm = get_llm()
    decision = structured(llm, RouteDecision).invoke(
        [("system", ROUTER_SYS), ("user", state["question"])])
    route = decision.route if decision.route in ("db", "doc", "hybrid") else "doc"
    return {"route": route, "trace": _t(state, f"router → {route}")}


def route_branch(state: HelpdeskState) -> str:
    return state["route"]


# ===========================================================================
# DB 도구 — 안전한 템플릿 SQL (LLM 이 intent 만 고르고, SQL 은 코드가 가짐)
# ===========================================================================
class DbIntent(BaseModel):
    intent: str = Field(description="'leave_balance' | 'carryover' | 'expense_status'")


DB_INTENT_SYS = """직원 개인 데이터 질문의 의도를 분류해 JSON 으로만 답하라.
- "leave_balance": 연차가 며칠 남았는지 등 잔여/사용 현황
- "carryover": 작년에서 이월된 연차 일수
- "expense_status": 경비/법인카드 정산 처리 상태
출력: {"intent": "..."}"""

SQL_TEMPLATES = {
    "leave_balance": (
        "SELECT total_days, carried_days, used_days, "
        "       total_days + carried_days - used_days AS remain "
        "FROM leaves WHERE emp_id = %s AND year = %s",
        "olive",
    ),
    "carryover": (
        "SELECT carried_days FROM leaves WHERE emp_id = %s AND year = %s",
        "olive",
    ),
    "expense_status": (
        "SELECT use_date, category, amount, status FROM expenses "
        "WHERE emp_id = %s ORDER BY use_date DESC LIMIT %s",
        "expense",
    ),
}


def run_db_query(intent: str, emp_id: str) -> tuple[str, str]:
    """(실행한 SQL 설명, 결과 텍스트) 반환."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT name, dept FROM employees WHERE emp_id = %s", (emp_id,))
        row = cur.fetchone()
        if not row:
            return "(employees 조회)", f"사번 {emp_id} 직원을 찾을 수 없습니다."
        name, dept = row

        if intent == "leave_balance":
            cur.execute(SQL_TEMPLATES["leave_balance"][0], (emp_id, TODAY.year))
            t, c, u, r = cur.fetchone()
            return (f"leaves({TODAY.year}) 조회",
                    f"{name}({dept}) — 올해 발생 {t}일 + 이월 {c}일 - 사용 {u}일 = 잔여 {r}일")
        if intent == "carryover":
            cur.execute(SQL_TEMPLATES["carryover"][0], (emp_id, TODAY.year))
            (c,) = cur.fetchone()
            return (f"leaves({TODAY.year}).carried_days 조회",
                    f"{name}({dept}) — 작년에서 이월된 연차 {c}일")
        # expense_status
        cur.execute(SQL_TEMPLATES["expense_status"][0], (emp_id, 5))
        rows = cur.fetchall()
        lines = [f"  {d} | {cat} | {amt:,}원 | {st}" for d, cat, amt, st in rows]
        return ("expenses 최근 5건 조회",
                f"{name}({dept}) 최근 경비 내역:\n" + "\n".join(lines))


# ===========================================================================
# 노드 3 — db_agent: 슬롯필링 포함 DB 조회
# ===========================================================================
def db_agent(state: HelpdeskState) -> dict:
    slots = state.get("slots", {})
    if "emp_id" not in slots:
        # ── 슬롯필링: 사번을 되묻고 이 질문을 보류 ──
        return {
            "answer": "개인 정보 조회를 위해 사번을 알려주시겠어요? (예: E1003)",
            "awaiting": "emp_id",
            "pending_question": state["original_question"],
            "pending_route": state["route"],
            "trace": _t(state, "db_agent: emp_id 없음 → 슬롯필링 질문"),
        }
    llm = get_llm()
    intent = structured(llm, DbIntent).invoke(
        [("system", DB_INTENT_SYS), ("user", state["question"])]).intent
    if intent not in SQL_TEMPLATES:
        intent = "leave_balance"
    sql_desc, result = run_db_query(intent, slots["emp_id"])
    answer = llm.invoke(
        [("system", "사내 헬프데스크 답변자. 조회 결과를 1~2문장의 정중한 한국어로 전달하라. "
                     "수치는 그대로 유지."),
         ("user", f"질문: {state['question']}\nDB 조회 결과: {result}")]).content
    return {"answer": answer,
            "trace": _t(state, f"db_agent: intent={intent}, {sql_desc}")}


# ===========================================================================
# 노드 4~7 — doc RAG: retrieve → grade → (rewrite 루프) → generate
#            (supp_03/04·05 의 채점·CRAG 루프 재사용)
# ===========================================================================
def retrieve(state: HelpdeskState) -> dict:
    vs = get_rules_vectorstore()
    docs = vs.as_retriever(search_kwargs={"k": 4}).invoke(state["question"])
    return {"docs": docs, "trace": _t(state, f"retrieve: {len(docs)}건")}


def grade(state: HelpdeskState) -> dict:
    llm = get_llm()
    relevant = []
    for d in state["docs"]:
        verdict = binary_yesno(
            llm,
            "검색된 규정 조항이 질문에 답하는 데 관련 있는지 판정하라.",
            f"질문: {state['question']}\n조항: {d.page_content[:500]}")
        if verdict == "yes":
            relevant.append(d)
    ok = len(relevant) > 0
    return {"docs": relevant, "grade_ok": ok,
            "trace": _t(state, f"grade: 관련 {len(relevant)}건 → {'합격' if ok else '불합격'}")}


def grade_branch(state: HelpdeskState) -> str:
    if state["grade_ok"]:
        return "generate"
    if state.get("rewrite_count", 0) < 2:
        return "rewrite"
    return "no_evidence"


def rewrite(state: HelpdeskState) -> dict:
    llm = get_llm()
    new_q = llm.invoke(
        [("system", "검색이 잘 되도록 질문을 회사 규정 용어로 한 문장으로 재작성하라. "
                     "재작성된 질문만 출력."),
         ("user", state["question"])]).content.strip()
    return {"question": new_q,
            "rewrite_count": state.get("rewrite_count", 0) + 1,
            "trace": _t(state, f"rewrite #{state.get('rewrite_count', 0) + 1}: {new_q!r}")}


def generate(state: HelpdeskState) -> dict:
    llm = get_llm()
    ctx = "\n\n".join(d.page_content for d in state["docs"])
    srcs = ", ".join(sorted({f"{d.metadata['source']} {d.metadata['article'].split('(')[0]}"
                             for d in state["docs"]}))
    answer = llm.invoke(
        [("system", "사내 헬프데스크 답변자. 아래 규정 조항만 근거로 2~4문장 한국어로 답하라. "
                     "조항에 없는 내용을 지어내지 마라."),
         ("user", f"질문: {state['original_question']}\n\n규정:\n{ctx}")]).content
    return {"answer": f"{answer}\n\n📎 근거: {srcs}",
            "trace": _t(state, f"generate: 근거 {len(state['docs'])}건 인용")}


def no_evidence(state: HelpdeskState) -> dict:
    # CRAG 의 정직한 실패 — 환각 대신 "근거 없음" 선언
    return {"answer": ("문의하신 내용은 현재 사내 규정에서 근거를 찾지 못했습니다. "
                       "규정에 명시되지 않은 사항이므로 인사팀(hr@dahee.co.kr)으로 "
                       "직접 문의해 주시기 바랍니다."),
            "trace": _t(state, "no_evidence: 재작성 2회 후에도 근거 없음 → 정직 응답")}


# ===========================================================================
# 노드 8 — hybrid: 분해 → 문서·DB 동시 수집 → 종합 (supp_03/03 재사용)
# ===========================================================================
class Decomposed(BaseModel):
    doc_question: str = Field(description="규정에서 찾을 질문")
    db_intent: str = Field(description="'leave_balance' | 'carryover' | 'expense_status'")


DECOMP_SYS = """질문을 (1)규정 문서에서 찾을 질문과 (2)DB 조회 의도로 분해해 JSON 으로만 답하라.
출력: {"doc_question": "...", "db_intent": "leave_balance|carryover|expense_status"}"""


def hybrid(state: HelpdeskState) -> dict:
    slots = state.get("slots", {})
    if "emp_id" not in slots:
        return {
            "answer": "개인 정보 조회를 위해 사번을 알려주시겠어요? (예: E1003)",
            "awaiting": "emp_id",
            "pending_question": state["original_question"],
            "pending_route": "hybrid",
            "trace": _t(state, "hybrid: emp_id 없음 → 슬롯필링 질문"),
        }
    llm = get_llm()
    dec = structured(llm, Decomposed).invoke(
        [("system", DECOMP_SYS), ("user", state["question"])])
    trace = _t(state, f"hybrid 분해: doc={dec.doc_question!r} / db={dec.db_intent}")

    # (1) 규정 검색
    vs = get_rules_vectorstore()
    docs = vs.as_retriever(search_kwargs={"k": 3}).invoke(dec.doc_question)
    ctx = "\n\n".join(d.page_content for d in docs)
    srcs = ", ".join(sorted({f"{d.metadata['source']} {d.metadata['article'].split('(')[0]}"
                             for d in docs}))
    # (2) DB 조회
    intent = dec.db_intent if dec.db_intent in SQL_TEMPLATES else "carryover"
    sql_desc, db_result = run_db_query(intent, slots["emp_id"])
    trace.append(f"hybrid 수집: 규정 {len(docs)}건 + DB({sql_desc})")

    # (3) 종합
    answer = llm.invoke(
        [("system", "사내 헬프데스크 답변자. 규정 근거와 본인 DB 현황을 결합해 "
                     f"3~4문장 한국어로 답하라. 오늘은 {TODAY.isoformat()} 이다. "
                     "기한이 있으면 남은 기간을 언급하라. 지어내지 마라."),
         ("user", f"질문: {state['original_question']}\n\n규정:\n{ctx}\n\n"
                  f"본인 현황(DB): {db_result}")]).content
    return {"answer": f"{answer}\n\n📎 근거: {srcs} + 사내 DB",
            "trace": trace}


# ===========================================================================
# 그래프 조립
# ===========================================================================
def build_graph():
    g = StateGraph(HelpdeskState)
    g.add_node("ingest", ingest)
    g.add_node("router", router)
    g.add_node("db_agent", db_agent)
    g.add_node("retrieve", retrieve)
    g.add_node("grade", grade)
    g.add_node("rewrite", rewrite)
    g.add_node("generate", generate)
    g.add_node("no_evidence", no_evidence)
    g.add_node("hybrid", hybrid)

    g.add_edge(START, "ingest")
    # ingest 후: 슬롯필링으로 route 가 복원됐으면 router 건너뜀
    g.add_conditional_edges(
        "ingest",
        lambda s: s.get("route") or "router",
        {"router": "router", "db": "db_agent", "doc": "retrieve", "hybrid": "hybrid"},
    )
    g.add_conditional_edges("router", route_branch,
                            {"db": "db_agent", "doc": "retrieve", "hybrid": "hybrid"})
    g.add_edge("retrieve", "grade")
    g.add_conditional_edges("grade", grade_branch,
                            {"generate": "generate", "rewrite": "rewrite",
                             "no_evidence": "no_evidence"})
    g.add_edge("rewrite", "retrieve")
    for end_node in ("db_agent", "generate", "no_evidence", "hybrid"):
        g.add_edge(end_node, END)

    return g.compile(checkpointer=MemorySaver())


def run_turn(graph, thread_id: str, text: str) -> dict:
    """한 턴 실행. route 는 매 턴 초기화하되 슬롯/awaiting 은 checkpointer 가 유지."""
    cfg = {"configurable": {"thread_id": thread_id}}
    return graph.invoke({"question": text, "route": "", "trace": []}, cfg)


if __name__ == "__main__":
    from _demo_common import banner
    banner("그래프 구조 확인")
    graph = build_graph()
    print(graph.get_graph().draw_ascii())
