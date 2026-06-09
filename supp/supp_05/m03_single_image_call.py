"""
m03_single_image_call.py — 이미지 한 장에 대한 단일 호출 (VQA)

가장 단순한 형태: chart.png 를 보고 "가장 큰 항목은?" 에 답하도록 시킨다.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import base64
from pathlib import Path

from langchain_core.messages import HumanMessage

from _assets import ensure_assets
from _common import get_vlm, banner, llm_unavailable


def encode_image(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode("utf-8")


def ask_about_image(llm, image_path: str, question: str) -> str:
    img_b64 = encode_image(image_path)
    message = HumanMessage(content=[
        {"type": "text", "text": question},
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{img_b64}"},
        },
    ])
    return llm.invoke([message]).content


def main() -> None:
    banner("VQA — chart.png 에 대한 단일 질문 호출")
    llm = get_vlm()
    if llm is None:
        llm_unavailable()
        return

    assets = ensure_assets()

    pairs = [
        (assets["chart"],   "이 차트에서 가장 큰 항목과 그 값을 알려줘."),
        (assets["scene"],   "이 이미지에 보이는 도형들을 색깔과 함께 한 줄로 정리해."),
        (assets["receipt"], "이 영수증의 TOTAL 금액과 DATE 를 정확히 추출해."),
    ]

    for img, q in pairs:
        print("\n" + "─" * 70)
        print(f"🖼  {Path(img).name}   ❓ {q}")
        try:
            ans = ask_about_image(llm, img, q)
            print(f"💬 {ans.strip()[:400]}")
        except Exception as e:
            print(f"⚠  {type(e).__name__}: {str(e)[:200]}")


if __name__ == "__main__":
    main()
