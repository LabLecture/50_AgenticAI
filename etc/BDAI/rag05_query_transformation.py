"""
rag05_query_transformation.py — MultiQueryRetriever (질의 자동 확장)
강의안 5-2 전략 3

원본 질의 1개 → LLM 이 다양한 표현으로 N개 변형 생성 → 각각 검색 → 합집합.
짧고 모호한 질의의 검색 누락을 줄인다.

🔑 LLM 호출이 필요. OPENROUTER_API_KEY 또는 OPENAI_API_KEY 가 없으면 안내 후 종료.
"""
import logging

# ⚠️ 강의안: from langchain.retrievers.multi_query import MultiQueryRetriever
#   langchain 1.x → langchain_classic
from langchain_classic.retrievers.multi_query import MultiQueryRetriever

from _common_rag import (
    SAMPLE_DOCS,
    get_vectorstore,
    get_llm,
    print_results,
    llm_unavailable_notice,
)


def main() -> None:
    llm = get_llm()
    if llm is None:
        llm_unavailable_notice("MultiQueryRetriever (LLM이 질의를 자동 변형)")
        return

    query = "RAG 검색 품질 올리려면?"

    # MultiQuery 가 생성한 변형 질의 만 보기 위해 해당 모듈 로거만 INFO 로 켠다.
    # ⚠️ logging.basicConfig(level=INFO) 를 쓰면 root logger 가 INFO 가 되어
    #    httpx / openai 등 다른 라이브러리의 INFO 메시지가 모두 콘솔로 쏟아진다.
    #    그래서 root 는 건드리지 않고, MultiQuery 로거에 별도 handler 를 붙여 격리.
    mq_logger = logging.getLogger("langchain_classic.retrievers.multi_query")
    mq_logger.setLevel(logging.INFO)
    if not mq_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("[MultiQuery] %(message)s"))
        mq_logger.addHandler(handler)
        mq_logger.propagate = False  # root 로 전파해 중복/혼합 출력 되는 것 방지

    # ── 1) 베이스 retriever ─────────────────────────
    vectorstore = get_vectorstore(SAMPLE_DOCS)
    base_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    # 비교: 원본 질의만 검색
    print_results("[원본 질의만] Vector Top-5", base_retriever.invoke(query), query)

    # ── 2) MultiQueryRetriever ──────────────────────
    multi_retriever = MultiQueryRetriever.from_llm(
        retriever=base_retriever,
        llm=llm,
    )
    docs = multi_retriever.invoke(query)
    print_results(
        "[MultiQuery] LLM이 생성한 변형 질의들의 결과 합집합",
        docs,
        query,
    )


if __name__ == "__main__":
    main()
