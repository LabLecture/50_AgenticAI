"""
05_compare_vector.py — 같은 질문, 벡터 RAG vs GraphRAG (supp_04/13 방식).

킬러 질문: "한빛유통 소속 인물 중 계약서에 서명하지 않은 사람은?"
  · 벡터 RAG: '한빛유통 소속'(doc04 이수진, doc01/08 박성호)과 '서명'(doc01)이
    여러 문서에 흩어져 있고, 집합의 차(소속 ∖ 서명자) 연산이라
    top-k 청크 안에서 답을 조립하기 어렵다 → 틀리거나 얼버무리기 쉽다.
  · GraphRAG: WORKS_FOR 와 SIGNED 관계의 집합 연산 한 줄 → 결정론적 정답 (이수진).
"""
from langchain_core.documents import Document
from langchain_chroma import Chroma

from _demo_common import get_llm, get_embeddings, get_neo4j_graph, banner, load_docs, CASE_ID

KILLER_Q = "한빛유통 소속 인물 중 계약서에 서명하지 않은 사람은 누구인가?"


def vector_rag_answer(llm) -> str:
    docs = [Document(page_content=d["text"], metadata={"doc_id": d["doc_id"]})
            for d in load_docs()]
    vs = Chroma.from_documents(docs, embedding=get_embeddings(),
                               collection_name="timeline_vector_cmp")
    hits = vs.as_retriever(search_kwargs={"k": 3}).invoke(KILLER_Q)
    print(f"  [벡터] top-3 청크: {[h.metadata['doc_id'] for h in hits]}")
    ctx = "\n\n".join(h.page_content for h in hits)
    return llm.invoke(
        [("system", "주어진 문서 발췌만 근거로 질문에 답하라. 발췌에서 확인 불가한 내용은 "
                     "'확인 불가'라고 답하라."),
         ("user", f"질문: {KILLER_Q}\n\n문서 발췌:\n{ctx}")]).content


def graph_rag_answer(graph) -> str:
    rows = graph.query("""
        MATCH (p:Party {kind: 'person', case: $c})-[:WORKS_FOR]->(:Party {name: '한빛유통'})
        WHERE NOT (p)-[:SIGNED]->(:Contract)
        RETURN p.name AS name, p.title AS title""", params={"c": CASE_ID})
    return ", ".join(f"{r['name']}({r['title']})" for r in rows) or "(없음)"


def main() -> None:
    banner("벡터 RAG vs GraphRAG — 집합 연산 질의 비교")
    llm = get_llm()
    graph = get_neo4j_graph(refresh_schema=False)
    if llm is None or graph is None:
        print("❌ env 미설정"); return

    print(f"❓ {KILLER_Q}\n")

    print("── ① 벡터 RAG (top-3 청크 → LLM) " + "─" * 35)
    print(f"  답: {vector_rag_answer(llm)}\n")

    print("── ② GraphRAG (WORKS_FOR ∖ SIGNED 집합 연산) " + "─" * 24)
    print("  Cypher: MATCH (p:Party{kind:'person'})-[:WORKS_FOR]->(:Party{name:'한빛유통'})")
    print("          WHERE NOT (p)-[:SIGNED]->(:Contract) RETURN p.name")
    print(f"  답: {graph_rag_answer(graph)}")
    print("\n  → 그래프 정답: 이수진(구매팀장) — 회신 1차(doc04)의 발신인이지만")
    print("    계약서(doc01) 서명인은 김재현·박성호 뿐이다. 벡터 RAG 는 top-k 에")
    print("    doc01·doc04 가 함께 들어와야만 답할 수 있고, 들어와도 집합 연산을")
    print("    LLM 추론에 의존한다. 그래프는 이 연산이 질의 언어 자체에 있다.")


if __name__ == "__main__":
    main()
