"""
m01_message_structure.py — 멀티모달 메시지 구조 (개념)

이미지를 LLM API 에 넘기는 두 방식 (base64 / URL) 과
멀티모달 메시지의 *블록 구조* 를 print 로 보여준다 (LLM 호출 없음).
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import base64
import json
from pathlib import Path

from _assets import ensure_assets
from _common import banner


def encode_image(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode("utf-8")


def main() -> None:
    banner("멀티모달 메시지 구조 — image 블록 + text 블록")
    assets = ensure_assets()
    chart_b64 = encode_image(assets["chart"])

    # OpenAI / Anthropic / LangChain 호환 (image_url 키 사용)
    message = {
        "role": "user",
        "content": [
            {"type": "text", "text": "이 차트에서 가장 큰 항목은?"},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{chart_b64[:40]}…"},
            },
        ],
    }

    print(json.dumps(message, ensure_ascii=False, indent=2))
    print(f"\n📦 base64 길이: {len(chart_b64):,} chars  (≈ {len(chart_b64)//1024} KB)")

    print("\n💡 핵심 포인트")
    print("  - content 는 *블록 리스트*. text/image_url 등 type 별 블록을 자유 조합 가능.")
    print("  - 같은 user 메시지에 이미지 여러 장 → '두 이미지 비교' 도 가능.")
    print("  - base64 data URI 형식: 'data:image/{형식};base64,{데이터}' — 접두사 누락 시 인식 실패.")


if __name__ == "__main__":
    main()
