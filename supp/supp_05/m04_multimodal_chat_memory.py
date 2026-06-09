"""
m04_multimodal_chat_memory.py — 멀티턴 이미지 대화

이미지를 1턴에 보내고, 2턴에서는 *이미지 재전송 없이* 후속 질문.
이력에 이미지 블록이 남아 있어 모델이 맥락을 유지한다.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import base64
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage

from _assets import ensure_assets
from _common import get_vlm, banner, llm_unavailable


def encode_image(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode("utf-8")


class MultimodalChat:
    def __init__(self, llm):
        self.llm = llm
        self.history = []

    def send(self, text: str, image_path: str | None = None) -> str:
        content = [{"type": "text", "text": text}]
        if image_path:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{encode_image(image_path)}"},
            })
        self.history.append(HumanMessage(content=content))
        reply = self.llm.invoke(self.history).content
        self.history.append(AIMessage(content=reply))
        return reply


def main() -> None:
    banner("멀티턴 — 이미지 1턴 + 후속 질문 2턴")
    llm = get_vlm()
    if llm is None:
        llm_unavailable()
        return

    assets = ensure_assets()
    chat = MultimodalChat(llm)

    # 1턴: 이미지 + 첫 질문
    print("\n[Turn 1] (이미지 첨부)")
    print("  USER : 이 차트의 항목들과 값을 알려줘.")
    r1 = chat.send("이 차트의 항목들과 값을 알려줘.", image_path=assets["chart"])
    print(f"  BOT  : {r1.strip()[:300]}")

    # 2턴: 텍스트만 — 모델이 1턴의 이미지를 기억해야 답할 수 있는 후속 질문
    print("\n[Turn 2] (이미지 재전송 X — 1턴 이미지 맥락 활용)")
    print("  USER : 그럼 가장 작은 항목은?")
    r2 = chat.send("그럼 가장 작은 항목은?")
    print(f"  BOT  : {r2.strip()[:300]}")

    print(f"\n📊 메시지 이력 길이: {len(chat.history)} (Human/AI 교차)")
    print("💡 토큰 절감 팁: 오래된 이미지 블록을 텍스트 요약으로 교체하거나, 최근 N개만 유지.")


if __name__ == "__main__":
    main()
