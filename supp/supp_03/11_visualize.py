"""
11_visualize.py — 그래프 구조 시각화

PNG 렌더에는 외부 mermaid CLI / pyppeteer 가 필요할 수 있다.
실패하면 Mermaid 텍스트를 콘솔에 출력 — https://mermaid.live 에서 붙여넣기 가능.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from pathlib import Path
import importlib
import sys

from _common import banner

sys.path.insert(0, str(Path(__file__).resolve().parent))
build_and_run = importlib.import_module("16_build_and_run")


def main() -> None:
    app = build_and_run.build_app()

    banner("Agentic RAG 그래프 — Mermaid 텍스트")
    print(app.get_graph().draw_mermaid())

    out = Path(__file__).resolve().parent / "agentic_rag_graph.png"
    try:
        png_bytes = app.get_graph().draw_mermaid_png()
        out.write_bytes(png_bytes)
        print(f"\n✅ PNG 저장: {out}")
    except Exception as e:
        print(f"\n⚠️  PNG 렌더 스킵 ({type(e).__name__}: {e})")
        print("   위 Mermaid 텍스트를 https://mermaid.live 에 붙여 확인 가능.")


if __name__ == "__main__":
    main()
