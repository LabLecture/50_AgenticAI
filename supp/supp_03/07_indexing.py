"""
08_indexing.py — 벡터스토어 구축 + Top-k 검색 확인

교안의 web scraping(Lilian Weng blog) 대신, _common.SAMPLE_DOCS 10 개 한국어
문서를 인덱싱한다. 이렇게 하면 인터넷 의존 없이 결정론적으로 데모 가능.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from _common import get_vectorstore, SAMPLE_DOCS, banner


def main() -> None:
    banner(f"인덱싱 — SAMPLE_DOCS {len(SAMPLE_DOCS)} 개를 인메모리 Chroma 에 적재")
    vs = get_vectorstore(SAMPLE_DOCS)
    retriever = vs.as_retriever(search_kwargs={"k": 4})

    test_queries = [
        "에이전트 메모리 종류",
        "CRAG 는 검색 결과를 어떻게 다루나",
        "LangGraph 의 조건부 엣지",
    ]

    for q in test_queries:
        docs = retriever.invoke(q)
        print(f"\n  🔍 query: {q!r}")
        for i, d in enumerate(docs, 1):
            print(f"    {i}. [{d.metadata['id']} / {d.metadata['topic']}] "
                  f"{d.page_content[:55]}…")


if __name__ == "__main__":
    main()
