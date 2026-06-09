"""
07_constrained_extraction.py — 스키마 제약으로 추출 품질 높이기

자유 추출 (06) 은 노드/관계 타입이 들쭉날쭉. 화이트리스트로 일관성↑.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer

from _common import get_llm, banner, llm_unavailable
from importlib import import_module
SAMPLE_TEXT = import_module("06_llm_graph_transformer").SAMPLE_TEXT


def main() -> None:
    banner("LLMGraphTransformer — 스키마 제약 (allowed_nodes / allowed_relationships)")
    llm = get_llm()
    if llm is None:
        llm_unavailable()
        return

    transformer = LLMGraphTransformer(
        llm=llm,
        allowed_nodes=["Person", "Company", "Product"],
        allowed_relationships=["FOUNDED", "DEVELOPED", "INVESTED_IN", "WORKED_AT"],
        ignore_tool_usage=True,   # free 모델 호환
    )

    docs = [Document(page_content=SAMPLE_TEXT.strip())]
    graph_docs = transformer.convert_to_graph_documents(docs)
    gd = graph_docs[0]

    print(f"\n📦 노드 ({len(gd.nodes)}개) — type 은 {{Person|Company|Product}} 내로 제한")
    for n in gd.nodes:
        print(f"  - ({n.id}, type={n.type})")

    print(f"\n🔗 관계 ({len(gd.relationships)}개) — type 은 화이트리스트 내로 제한")
    for r in gd.relationships:
        print(f"  - ({r.source.id})-[:{r.type}]->({r.target.id})")


if __name__ == "__main__":
    main()
