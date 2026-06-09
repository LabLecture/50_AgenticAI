"""
13_subagents.py — Supervisor 패턴의 *작업자(worker) sub-agent* 3종

08~10 의 단일 그래프 노드 중 *외부 자원* 을 다루던 3 개를 sub-agent 로 재구성:
  - retrieve_agent     : 사내 벡터DB 검색 담당
  - grade_agent        : 검색된 문서의 질문 관련성 채점 담당
  - web_search_agent   : 외부 DuckDuckGo 웹 검색 담당

⚠ supervisor 가 책임지는 *추론* 기능 (generate / transform_query) 은 14_supervisor.py 로 이동.
   sub-agent 는 "도구를 잘 쓰는 전문가" 역할에만 집중한다.

내부적으로 08_nodes 의 retrieve / grade_documents / web_search 를 *그대로 위임* 한다.
이렇게 하면 09_conditional_edges.py / 10_build_and_run.py 의 로직과 1:1 비교가 가능하다.
"""
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # supp/ → _common.py
sys.path.insert(0, str(Path(__file__).resolve().parent))          # supp_03/ → 08_nodes

_nodes = importlib.import_module("08_nodes")    # retrieve / grade_documents / web_search 재사용


# ─────────────────────────────────────────────────────────────
# Sub-agent 1: Retriever
# ─────────────────────────────────────────────────────────────
def retrieve_agent(state) -> dict:
    """🤖 Retriever sub-agent — 사내 벡터DB 에서 question 으로 top-k 검색."""
    print("  🤖 [retrieve_agent] 사내 벡터DB 검색...")
    out = _nodes.retrieve(state)
    out["last_action"] = "retrieve"
    print(f"     → {len(out['documents'])} 개 doc 회수")
    return out


# ─────────────────────────────────────────────────────────────
# Sub-agent 2: Grader
# ─────────────────────────────────────────────────────────────
def grade_agent(state) -> dict:
    """🤖 Grader sub-agent — 각 문서의 질문 관련성 yes/no 채점."""
    print("  🤖 [grade_agent] 관련성 채점...")
    out = _nodes.grade_documents(state)
    out["last_action"] = "grade"
    out["web_search_needed"] = out.pop("web_search")    # 키 명 명확화
    return out


# ─────────────────────────────────────────────────────────────
# Sub-agent 3: Web searcher
# ─────────────────────────────────────────────────────────────
def web_search_agent(state) -> dict:
    """🤖 WebSearch sub-agent — 외부 DuckDuckGo 검색 1 회."""
    print("  🤖 [web_search_agent] 외부 웹 검색...")
    out = _nodes.web_search(state)
    out["last_action"] = "web_search"
    print(f"     → 현재 documents 총 {len(out['documents'])} 개")
    return out


# 단독 실행 시 시그니처만 확인
if __name__ == "__main__":
    print("13_subagents.py — sub-agent 함수 시그니처")
    for fn in (retrieve_agent, grade_agent, web_search_agent):
        print(f"  - {fn.__name__:<18} : (state) → dict")
    print("\n  16_build_and_run.py 에서 supervisor 그래프의 노드로 등록된다.")
