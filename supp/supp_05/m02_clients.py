"""
m02_clients.py — 멀티모달 클라이언트 선택 가이드

(A) OpenRouter vision 모델 (기본 Gemma 4 26B A4B) → ChatOpenAI 인터페이스
(B) 로컬 Ollama 경로 (langchain_ollama) — 이 강의 환경에선 미설치, 코드 형태만 안내
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import os
from _common import get_vlm, banner


def main() -> None:
    banner("멀티모달 클라이언트 — OpenRouter Gemma 4 vision / Ollama 로컬")

    vlm = get_vlm()
    if vlm is None:
        print("⚠️ OPENROUTER_API_KEY 미설정")
    else:
        print(f"  ✅ (A) OpenRouter 경로")
        print(f"     model={vlm.model_name}")
        print(f"     base_url={vlm.openai_api_base}")
        print(f"     timeout={vlm.request_timeout}s, max_retries={vlm.max_retries}")

    print(f"\n  ▶ (B) 로컬 Ollama 경로 (의존성 별도 설치 필요)")
    print("     from langchain_ollama import ChatOllama")
    print("     local_llm = ChatOllama(model='llama3.2-vision', temperature=0)")

    print(f"\n  📋 OpenRouter vision 모델 (.env 의 OPENROUTER_VISION_MODEL 로 교체)")
    # [참고] 기존 default: nvidia/nemotron-3.5-super-vl:free
    candidates = [
        "google/gemma-4-26b-a4b-it           (default, 유료·저가)",
        "google/gemma-4-26b-a4b-it:free      (free 변형, 429 잦음)",
        "google/gemma-4-31b-it:free",
        "nvidia/nemotron-3.5-super-vl:free",
    ]
    for c in candidates:
        print(f"    - {c}")


if __name__ == "__main__":
    main()
