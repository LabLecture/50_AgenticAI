"""
demo_timeline 공통 모듈 — supp/_common 재사용 + 사건 문서 로딩.

Neo4j 는 supp_04 의 neo4j-graphrag 컨테이너(7687)를 그대로 쓴다.
데모 그래프는 모든 노드에 `case` 프로퍼티('CT-2025-017')를 박아
기존 실습 데이터와 구분하고, 리셋 시 데모 노드만 지운다.
"""
import sys as _sys
from pathlib import Path as _Path

_SUPP = _Path(__file__).resolve().parent.parent.parent
_sys.path.insert(0, str(_SUPP))

from _common import (  # noqa: E402,F401
    get_llm, get_embeddings, get_neo4j_graph, structured, banner,
)

DATA_DIR = _Path(__file__).resolve().parent / "data"
EXTRACT_JSON = _Path(__file__).resolve().parent / "extracted.json"
CASE_ID = "CT-2025-017"


def load_docs() -> list[dict]:
    """data/*.md → [{doc_id, title, text}] (파일명 순 = 대체로 시간 순)."""
    docs = []
    for md in sorted(DATA_DIR.glob("doc*.md")):
        text = md.read_text(encoding="utf-8")
        docs.append({
            "doc_id": md.stem.split("_")[0],          # doc01 ...
            "title": md.stem.split("_", 1)[1],        # 공급계약서 ...
            "text": text,
        })
    return docs


def reset_demo_graph(graph) -> None:
    """이 데모(case=CT-2025-017)의 노드만 삭제 — 다른 실습 데이터 보존."""
    graph.query("MATCH (n {case: $c}) DETACH DELETE n", params={"c": CASE_ID})
