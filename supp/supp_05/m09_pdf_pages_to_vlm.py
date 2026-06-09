"""
m09_pdf_pages_to_vlm.py — PDF 페이지를 이미지로 렌더 → VLM 으로 분석

`pdf2image` 대신 `PyMuPDF (fitz)` 사용 — Windows 에서 poppler 별도 설치 불필요.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import base64
from pathlib import Path

from langchain_core.messages import HumanMessage

from _assets import ensure_assets
from _common import get_vlm, banner, llm_unavailable


def pdf_to_images(pdf_path: str, dpi: int = 150, max_pages: int = 3):
    """각 페이지를 PNG bytes 로 반환."""
    import fitz  # PyMuPDF
    doc = fitz.open(pdf_path)
    images = []
    for i, page in enumerate(doc):
        if i >= max_pages:
            break
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        images.append(pix.tobytes("png"))
    return images


def ask_about_pdf(llm, pdf_path: str, question: str) -> str:
    page_pngs = pdf_to_images(pdf_path)
    content = [{"type": "text", "text": question}]
    for png in page_pngs:
        b64 = base64.b64encode(png).decode("utf-8")
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}"},
        })
    return llm.invoke([HumanMessage(content=content)]).content


def main() -> None:
    banner("문서 이미지 처리 — PDF 페이지 → VLM (PyMuPDF)")
    llm = get_vlm()
    if llm is None:
        llm_unavailable()
        return

    assets = ensure_assets()
    pdf = assets["invoice"]
    pages = pdf_to_images(pdf)
    print(f"  ▶ PDF: {Path(pdf).name}, {len(pages)} 페이지를 PNG 로 렌더")

    question = "이 청구서의 총액(TOTAL)과 마감일(Due Date)을 정확히 추출해."
    print(f"\n❓ {question}")
    try:
        ans = ask_about_pdf(llm, pdf, question)
        print(f"💬 {ans.strip()[:400]}")
    except Exception as e:
        print(f"⚠ {type(e).__name__}: {str(e)[:200]}")

    print(f"\n💡 텍스트 추출이 안 되는 스캔 PDF / 복잡 레이아웃 문서에서 *가장 강력한* 옵션.")
    print(f"   대안: pypdf 텍스트 추출 (실패 시 폴백) → VLM 이미지 입력 — 보충 ① Agentic RAG 의 채점 단계와 연결 가능.")


if __name__ == "__main__":
    main()
