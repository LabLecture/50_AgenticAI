"""
m07_stt_whisper.py — 음성 → 텍스트 (faster-whisper, 로컬 무료)

OpenAI Whisper API 대신 로컬 `faster-whisper` 사용 — API 키 불필요.
오디오가 없으면 edge-tts 로 한국어 샘플을 만들어 STT 데모.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import asyncio
from pathlib import Path

from _common import banner


SAMPLE_AUDIO = Path(__file__).resolve().parent / "sample_images" / "sample_voice.mp3"
SAMPLE_TEXT_FOR_TTS = (
    "안녕하세요. 이것은 멀티모달 챗봇의 음성 인식 테스트입니다. "
    "지금부터 RAG 시스템에 대해 질문하겠습니다."
)


async def _make_sample_audio() -> None:
    """edge-tts 로 데모 mp3 한 개 생성."""
    if SAMPLE_AUDIO.exists():
        return
    import edge_tts
    SAMPLE_AUDIO.parent.mkdir(exist_ok=True)
    voice = "ko-KR-SunHiNeural"
    comm = edge_tts.Communicate(SAMPLE_TEXT_FOR_TTS, voice)
    await comm.save(str(SAMPLE_AUDIO))


def main() -> None:
    banner("STT — faster-whisper (로컬, API 키 불필요)")
    asyncio.run(_make_sample_audio())
    print(f"  ▶ 입력 오디오: {SAMPLE_AUDIO.name}  ({SAMPLE_AUDIO.stat().st_size:,} bytes)")
    print(f"  ▶ 원본 텍스트: {SAMPLE_TEXT_FOR_TTS}")

    print("\n[STT] faster-whisper 로딩 중 (최초 호출 시 ~150MB 다운로드)…")
    from faster_whisper import WhisperModel
    # "small" 은 ~470MB, "base" 는 ~140MB. 강의 데모는 base 로 충분.
    model = WhisperModel("base", device="cpu", compute_type="int8")

    print("[STT] 변환 중…")
    segments, info = model.transcribe(str(SAMPLE_AUDIO), language="ko")
    text = " ".join(s.text for s in segments).strip()

    print(f"\n  language={info.language}  prob={info.language_probability:.2f}")
    print(f"  📝 변환 결과: {text}")
    print(f"\n💡 변환된 텍스트를 챗봇 입력으로 그대로 사용 가능 → 음성 어시스턴트 흐름.")


if __name__ == "__main__":
    main()
