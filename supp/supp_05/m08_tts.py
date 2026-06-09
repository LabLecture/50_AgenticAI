"""
m08_tts.py — 텍스트 → 음성 (edge-tts, 무료)

OpenAI TTS API 대신 Microsoft Edge TTS — 무료, 키 불필요, 한국어 음성 다수.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import asyncio
from pathlib import Path

from _common import banner


OUT_DIR = Path(__file__).resolve().parent / "sample_images"
SAMPLE_TEXT = (
    "안녕하세요. 멀티모달 챗봇의 답변을 음성으로 전달합니다. "
    "오늘 청구 총액은 158달러 80센트이며, 마감일은 7월 2일입니다."
)


async def speak(text: str, out_path: Path, voice: str = "ko-KR-SunHiNeural") -> None:
    import edge_tts
    comm = edge_tts.Communicate(text, voice)
    await comm.save(str(out_path))


def main() -> None:
    banner("TTS — edge-tts (Microsoft Edge 음성, 무료)")
    OUT_DIR.mkdir(exist_ok=True)

    out = OUT_DIR / "tts_reply.mp3"
    asyncio.run(speak(SAMPLE_TEXT, out))

    size = out.stat().st_size
    print(f"  입력 텍스트: {SAMPLE_TEXT}")
    print(f"  ✅ 출력: {out.name}  ({size:,} bytes)")

    print(f"\n💡 사용 가능한 한국어 음성 예")
    print("  - ko-KR-SunHiNeural   (여성, default)")
    print("  - ko-KR-InJoonNeural  (남성)")
    print("  - ko-KR-BongJinNeural (남성)")

    print(f"\n💡 STT(m07) + 챗봇(m04) + TTS(m08) → '말로 묻고 말로 답하는' 음성 어시스턴트 루프")


if __name__ == "__main__":
    main()
