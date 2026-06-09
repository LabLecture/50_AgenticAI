"""
12_react_rag_agent.py — ReAct 패턴의 RAG 에이전트 (비교군)

10_build_and_run.py 의 *명시적 그래프* 와 대비.
ReAct = 검색을 "도구" 로 두고 LLM 이 생각 → 검색 → 관찰 → 다시 생각 을 자율적으로 반복.
유연하지만 예측 가능성이 낮고 비용이 들쭉날쭉한 단점.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from _common import get_llm, get_vectorstore, SAMPLE_DOCS, web_search_fn, banner, llm_unavailable


_retriever = get_vectorstore(SAMPLE_DOCS).as_retriever(search_kwargs={"k": 4})


@tool
def search_knowledge_base(query: str) -> str:
    """사내 지식베이스(벡터 DB)에서 관련 문서를 검색한다.
    AI 에이전트 메모리·도구 사용·Self-RAG·CRAG 등 RAG 관련 질문에 사용."""
    docs = _retriever.invoke(query)
    return "\n\n".join(d.page_content for d in docs)


@tool
def search_web(query: str) -> str:
    """최신 뉴스·시세·실시간 정보가 필요한 경우 외부 웹을 검색한다."""
    return web_search_fn(query, k=3)


def main() -> None:
    llm = get_llm()
    if llm is None:
        llm_unavailable()
        return

    agent = create_react_agent(
        model=llm,
        tools=[search_knowledge_base, search_web],
    )

    banner("ReAct Agent — 검색을 '도구' 로 두고 자율적으로 호출")
    result = agent.invoke({
        "messages": [("user", "에이전트 메모리 종류를 정리해줘. 한국어로 간결히.")],
    })

    print("\n💬 메시지 trace (간략):")
    for msg in result["messages"]:
        kind = type(msg).__name__
        content_preview = (msg.content or "")[:120].replace("\n", " ")
        tool_calls = getattr(msg, "tool_calls", None) or []
        if tool_calls:
            for tc in tool_calls:
                print(f"  [{kind}] tool_call → {tc['name']}({tc['args']})")
        else:
            print(f"  [{kind}] {content_preview}")

    print("\n📝 최종 답변")
    print("-" * 70)
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
