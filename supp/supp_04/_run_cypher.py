"""
_run_cypher.py — .cypher 파일을 줄 단위로 실행하는 단순 러너

사용:
    python _run_cypher.py 03_cypher_basics.cypher
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import re
import sys
from pathlib import Path

from _common import get_neo4j_graph


def run(path: str) -> None:
    text = Path(path).read_text(encoding="utf-8")
    # // 한 줄 주석 제거
    text = re.sub(r"//[^\n]*", "", text)
    # ; 로 분할
    statements = [s.strip() for s in text.split(";") if s.strip()]

    graph = get_neo4j_graph(refresh_schema=False)
    if graph is None:
        print("❌ NEO4J_* env 미설정")
        sys.exit(1)

    print(f"📄 {path} — {len(statements)} 개 Cypher 문")
    print("=" * 70)
    for i, stmt in enumerate(statements, 1):
        snippet = stmt.replace("\n", " ").strip()[:80]
        try:
            result = graph.query(stmt)
            if result:
                print(f"[{i}] {snippet}…")
                for row in result[:10]:
                    print(f"    {dict(row)}")
            else:
                print(f"[{i}] {snippet}…  (no rows)")
        except Exception as e:
            print(f"[{i}] ❌ {snippet}…  → {type(e).__name__}: {str(e)[:80]}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용: python _run_cypher.py <파일.cypher>")
        sys.exit(2)
    run(sys.argv[1])
