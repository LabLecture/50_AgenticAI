"""
demo_helpdesk 공통 모듈 — DB 연결 + 규정 문서 벡터스토어.

LLM/임베딩은 supp/_common.py 를 그대로 재사용한다(OpenRouter + e5-small).
PostgreSQL 은 전용 Docker 컨테이너(helpdesk-pg, 포트 5433)를 쓴다:

  docker run -d --name helpdesk-pg \
    -e POSTGRES_USER=demo -e POSTGRES_PASSWORD=demo1234 -e POSTGRES_DB=helpdesk \
    -p 5433:5432 postgres:16-alpine
"""
import os
import sys as _sys
from pathlib import Path as _Path

# supp/ 루트를 import 경로에 추가 → _common 재사용
_SUPP = _Path(__file__).resolve().parent.parent.parent
_sys.path.insert(0, str(_SUPP))

from _common import get_llm, get_embeddings, structured, binary_yesno, banner  # noqa: E402,F401

DATA_DIR = _Path(__file__).resolve().parent / "data"

PG_DSN = os.getenv(
    "HELPDESK_PG_DSN",
    "host=localhost port=5433 dbname=helpdesk user=demo password=demo1234",
)


def get_conn():
    """psycopg3 커넥션. autocommit 으로 데모 단순화."""
    import psycopg
    return psycopg.connect(PG_DSN, autocommit=True)


# ── 규정 문서 → 조항 단위 청킹 → 인메모리 Chroma ──────────────────────────
_VS = None


def get_rules_vectorstore():
    """규정 md 3종을 '## 장' + '제n조' 단위로 청킹해 Chroma 에 적재 (1회 캐시).

    조항 단위 청킹 이유: 규정 문서는 조항이 독립적 의미 단위라
    RecursiveCharacterTextSplitter 보다 검색 정밀도가 훨씬 좋다.
    """
    global _VS
    if _VS is not None:
        return _VS

    import re
    from langchain_core.documents import Document
    from langchain_chroma import Chroma

    docs = []
    for md in sorted(DATA_DIR.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        source = md.stem  # 취업규칙 / 복무규정 / 경비처리지침
        # "**제n조(제목)**" 기준으로 분할하되, 직전의 "## 장" 헤더를 컨텍스트로 부착
        chapter = ""
        article = None
        buf: list[str] = []

        def flush():
            if article and buf:
                docs.append(Document(
                    page_content=f"[{source} {chapter}] {article}\n" + "\n".join(buf).strip(),
                    metadata={"source": source, "chapter": chapter, "article": article},
                ))

        for line in text.splitlines():
            ch = re.match(r"^##\s+(.+)$", line)
            art = re.match(r"^\*\*(제\d+조[^*]*)\*\*\s*(.*)$", line)
            if ch:
                flush(); buf, article = [], None
                chapter = ch.group(1).strip()
            elif art:
                flush(); buf = [art.group(2)] if art.group(2) else []
                article = art.group(1).strip()
            elif article is not None:
                buf.append(line)
        flush()

    _VS = Chroma.from_documents(docs, embedding=get_embeddings(),
                                collection_name="dahee_rules")
    print(f"  [indexing] 규정 조항 {len(docs)}개 청크 적재 완료")
    return _VS
