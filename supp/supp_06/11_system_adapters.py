"""
11_system_adapters.py — 평가 대상 RAG 시스템을 동일 인터페이스로 wrap

각 시스템은 `(answer, contexts)` 튜플을 반환하는 함수 1 개로 정규화.
12_run_comparison.py 가 이 어댑터들을 SYSTEMS dict 에서 골라 평가에 돌린다.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
import importlib
import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from _common import get_llm, get_vectorstore, SAMPLE_DOCS, banner


# ─────────────────────────────────────────────────────────────────────
# (A) Vector RAG (베이스라인) — 단순 vector 검색 + LLM 생성
# ─────────────────────────────────────────────────────────────────────
_vec_retriever = None
_vec_chain = None


def _init_vector():
    global _vec_retriever, _vec_chain
    if _vec_retriever is not None:
        return
    vs = get_vectorstore(SAMPLE_DOCS)
    _vec_retriever = vs.as_retriever(search_kwargs={"k": 4})
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "다음 컨텍스트만 근거로 한국어로 2 문장 이내로 답하라.\n\n{context}"),
        ("human", "{question}"),
    ])
    _vec_chain = prompt | llm | StrOutputParser()


def run_vector_rag(question: str) -> tuple[str, list[str]]:
    _init_vector()
    docs = _vec_retriever.invoke(question)
    contexts = [d.page_content for d in docs]
    answer = _vec_chain.invoke({"context": "\n\n".join(contexts), "question": question})
    return answer, contexts


# ─────────────────────────────────────────────────────────────────────
# (B) Agentic RAG — supp/supp_03/11_build_and_run.py 의 build_app() 재사용
# ─────────────────────────────────────────────────────────────────────
_agentic_app = None


def _init_agentic():
    global _agentic_app
    if _agentic_app is not None:
        return
    # supp_03 디렉토리를 sys.path 에 추가해 m11_build_and_run 을 importlib 로 로드
    supp_03 = _Path(__file__).resolve().parent.parent / "supp_03"
    _sys.path.insert(0, str(supp_03))
    m11 = importlib.import_module("11_build_and_run")
    _agentic_app = m11.build_app()


def run_agentic_rag(question: str) -> tuple[str, list[str]]:
    _init_agentic()
    inputs = {"question": question, "retry_count": 0}
    final = {}
    for step in _agentic_app.stream(inputs, {"recursion_limit": 25}):
        for _, payload in step.items():
            final.update(payload)
    return final.get("generation", ""), final.get("documents", [])


# ─────────────────────────────────────────────────────────────────────
# (C) Graph RAG — supp/supp_04 의 GraphCypherQAChain. Neo4j 미가용 시 graceful skip.
# ─────────────────────────────────────────────────────────────────────
def run_graph_rag(question: str) -> tuple[str, list[str]]:
    if not os.getenv("NEO4J_URI"):
        return "[graph-rag skipped: NEO4J_URI not set]", []
    try:
        from langchain_neo4j import GraphCypherQAChain
        from _common import get_neo4j_graph
        graph = get_neo4j_graph()
        if graph is None:
            return "[graph-rag skipped: Neo4j not reachable]", []
        chain = GraphCypherQAChain.from_llm(
            llm=get_llm(), graph=graph, verbose=False,
            allow_dangerous_requests=True,
        )
        out = chain.invoke({"query": question})
        return out["result"], []   # GraphCypherQAChain 은 contexts 미반환
    except Exception as e:
        return f"[graph-rag error: {type(e).__name__}: {str(e)[:80]}]", []


SYSTEMS = {
    "vector":  run_vector_rag,
    "agentic": run_agentic_rag,
    "graph":   run_graph_rag,
}


# ─────────────────────────────────────────────────────────────────────
# 단독 실행 — 한 질문에 3 시스템 답변/컨텍스트 비교
# ─────────────────────────────────────────────────────────────────────
def main() -> None:
    banner("System Adapters — 같은 질문, 3 시스템 답변")
    q = "Self-RAG 와 CRAG 의 핵심 차이는?"
    print(f"\n  ❓ {q}")
    for name, fn in SYSTEMS.items():
        try:
            ans, ctxs = fn(q)
            print(f"\n  [{name}]")
            print(f"    answer  : {ans.strip()[:200]}")
            print(f"    ctxs    : {len(ctxs)} 개")
        except Exception as e:
            print(f"\n  [{name}] ⚠ {type(e).__name__}: {str(e)[:120]}")


if __name__ == "__main__":
    main()
