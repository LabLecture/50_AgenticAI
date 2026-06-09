"""
08_nodes.py — 그래프 노드 함수 정의

이 모듈은 10_build_and_run.py 에서 import 한다.
각 노드 함수는 GraphState 를 입력받아 *갱신할 필드만 담은 dict* 를 반환한다.

⚠ structured output 은 free 모델에서 불안정하므로 binary_yesno helper 사용.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from _common import (
    get_llm, binary_yesno, get_vectorstore, SAMPLE_DOCS, web_search_fn, banner,
)


# ── 공유 LLM / retriever / chain — lazily 초기화 ────────────
_llm = None
_retriever = None
_rewriter = None
_rag_chain = None


def _init():
    global _llm, _retriever, _rewriter, _rag_chain
    if _llm is not None:
        return
    _llm = get_llm()
    _retriever = get_vectorstore(SAMPLE_DOCS).as_retriever(search_kwargs={"k": 4})

    _rewriter = (
        ChatPromptTemplate.from_messages([
            ("system",
             "질문을 벡터 검색에 더 적합하도록 한 줄로 재작성. 결과만 출력."),
            ("human", "원본: {question}"),
        ])
        | _llm | StrOutputParser()
    )

    _rag_chain = (
        ChatPromptTemplate.from_messages([
            ("system",
             "다음 컨텍스트만 근거로 한국어로 3 문장 이내로 답하라. "
             "모르면 모른다고 하라.\n\n{context}"),
            ("human", "{question}"),
        ])
        | _llm | StrOutputParser()
    )


# ===========================================================================
# 노드 함수 5 종
# ===========================================================================
def retrieve(state) -> dict:
    _init()
    print("--- RETRIEVE ---")
    docs = _retriever.invoke(state["question"])
    return {
        "documents": [d.page_content for d in docs],
        "retry_count": state.get("retry_count", 0),
    }


def grade_documents(state) -> dict:
    _init()
    print("--- GRADE DOCUMENTS ---")
    question, docs = state["question"], state["documents"]
    kept = []
    for d in docs:
        score = binary_yesno(
            _llm,
            "문서가 질문에 답하는 데 관련이 있으면 yes, 아니면 no.",
            f"문서:\n{d}\n\n질문: {question}",
        )
        if score == "yes":
            kept.append(d)
    web_flag = "Yes" if not kept else "No"
    print(f"    {len(kept)}/{len(docs)} 통과 → web_search={web_flag}")
    return {"documents": kept, "web_search": web_flag}


def generate(state) -> dict:
    _init()
    print("--- GENERATE ---")
    answer = _rag_chain.invoke({
        "context": "\n\n".join(state["documents"]),
        "question": state["question"],
    })
    return {"generation": answer}


def transform_query(state) -> dict:
    _init()
    print("--- TRANSFORM QUERY ---")
    better = _rewriter.invoke({"question": state["question"]}).strip()
    print(f"    재작성: {better}")
    return {
        "question": better,
        "retry_count": state.get("retry_count", 0) + 1,
    }


def web_search(state) -> dict:
    _init()
    print("--- WEB SEARCH (DuckDuckGo) ---")
    text = web_search_fn(state["question"], k=3)
    docs = state.get("documents", []) + [text]
    return {"documents": docs}


# ===========================================================================
# 단독 실행 시 노드 시그니처만 확인
# ===========================================================================
if __name__ == "__main__":
    banner("08_nodes.py — 노드 함수 시그니처 확인")
    for fn in [retrieve, grade_documents, generate, transform_query, web_search]:
        print(f"  - {fn.__name__:<18} : (state) → dict")
    print("\n  이 모듈은 10_build_and_run.py 에서 import 된다.")
