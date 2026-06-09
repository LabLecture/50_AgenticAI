"""
_assets.py — 멀티모달 실습용 테스트 이미지/오디오 자동 생성

처음 실행 시 sample_images/ 폴더에 PIL 로 그린 3 종 이미지 + 간단한 PDF 를 만든다.
이후 호출은 캐시된 파일을 재사용.
"""
from __future__ import annotations

from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent / "sample_images"


def _make_chart_png(path: Path) -> None:
    """막대그래프 — 3 막대 (A=30, B=80, C=50). VLM 이 '가장 큰 항목은?' 에 답할 수 있는 데이터."""
    from PIL import Image, ImageDraw, ImageFont

    W, H = 400, 280
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    d.text((140, 10), "Sales by Region", fill="black", font=font)

    labels = ["A", "B", "C"]
    values = [30, 80, 50]
    colors = ["#3b82f6", "#ef4444", "#10b981"]
    bar_w = 60
    gap = 40
    base_y = 240
    for i, (lab, v, col) in enumerate(zip(labels, values, colors)):
        x = 60 + i * (bar_w + gap)
        bar_h = v * 2  # 최대 160 px
        d.rectangle([x, base_y - bar_h, x + bar_w, base_y], fill=col)
        d.text((x + 25, base_y + 10), lab, fill="black", font=font)
        d.text((x + 20, base_y - bar_h - 18), str(v), fill="black", font=font)

    img.save(path)


def _make_scene_png(path: Path) -> None:
    """장면 — 빨간 사각형 + 파란 원 + 노란 삼각형. VLM 이 도형 식별 가능."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (400, 280), "#f5f5f5")
    d = ImageDraw.Draw(img)
    d.rectangle([40, 60, 140, 200], fill="#ef4444")   # 빨간 사각형
    d.ellipse([170, 60, 290, 180], fill="#3b82f6")    # 파란 원
    d.polygon([(330, 200), (390, 200), (360, 80)], fill="#facc15")  # 노란 삼각형
    img.save(path)


def _make_receipt_png(path: Path) -> None:
    """영수증 — TOTAL / DATE 가 명확. VLM OCR 능력 테스트."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (350, 380), "white")
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    lines = [
        "===== COFFEE SHOP =====",
        "DATE:  2026-06-02",
        "ORDER: #1234",
        "-----------------------",
        "Americano        $4.50",
        "Latte            $5.00",
        "Bagel            $3.50",
        "-----------------------",
        "SUBTOTAL        $13.00",
        "TAX  (8%)        $1.04",
        "-----------------------",
        "TOTAL           $14.04",
        "",
        "Thank you, come again!",
    ]
    y = 20
    for ln in lines:
        d.text((20, y), ln, fill="black", font=font)
        y += 22

    img.save(path)


def _make_demo_pdf(path: Path) -> None:
    """간단한 1 페이지 PDF (PyMuPDF). VLM 으로 페이지 이미지 분석."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return  # 없으면 생략

    doc = fitz.open()
    page = doc.new_page(width=420, height=550)
    text = (
        "INVOICE\n\n"
        "Bill To: Acme Corp\n"
        "Date:    2026-06-02\n"
        "Invoice: INV-2026-001\n\n"
        "Description           Qty    Price\n"
        "-------------------------------------\n"
        "Cloud GPU Hour         24    $1.20\n"
        "API Calls (1k)         50    $0.30\n"
        "Support (hr)            2    $50.00\n"
        "-------------------------------------\n"
        "                          TOTAL: $158.80\n\n"
        "Due Date: 2026-07-02\n"
    )
    page.insert_text((40, 50), text, fontname="helv", fontsize=11)
    doc.save(str(path))
    doc.close()


def ensure_assets() -> dict:
    """모든 자산 파일을 만들고 경로 dict 반환."""
    ASSETS_DIR.mkdir(exist_ok=True)
    paths = {
        "chart":   ASSETS_DIR / "chart.png",
        "scene":   ASSETS_DIR / "scene.png",
        "receipt": ASSETS_DIR / "receipt.png",
        "invoice": ASSETS_DIR / "invoice.pdf",
    }
    if not paths["chart"].exists():
        _make_chart_png(paths["chart"])
    if not paths["scene"].exists():
        _make_scene_png(paths["scene"])
    if not paths["receipt"].exists():
        _make_receipt_png(paths["receipt"])
    if not paths["invoice"].exists():
        _make_demo_pdf(paths["invoice"])
    return {k: str(v) for k, v in paths.items()}


if __name__ == "__main__":
    paths = ensure_assets()
    for k, p in paths.items():
        print(f"  {k:8s}: {p}")
