"""
m02_clients.py — 멀티모달 클라이언트 선택 가이드

(A) OpenRouter free vision 모델 → ChatOpenAI 인터페이스
(B) 로컬 Ollama 경로 (langchain_ollama) — 이 강의 환경에선 미설치, 코드 형태만 안내
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import os
from _common import get_vlm, banner


def main() -> None:
    banner("멀티모달 클라이언트 — OpenRouter free vision / Ollama 로컬")

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

    print(f"\n  📋 OpenRouter free vision 모델 (.env 의 OPENROUTER_VISION_MODEL 로 교체)")
    candidates = [
        "google/gemma-4-31b-it:free          (default)",
        "google/gemma-4-26b-a4b-it:free      (좀 더 작은 변형)",
        "nvidia/nemotron-nano-12b-v2-vl:free (소형 VL 전문 모델)",
        "moonshotai/kimi-k2.6:free",
        "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    ]
    for c in candidates:
        print(f"    - {c}")


if __name__ == "__main__":
    main()
