"""
m05_gradio_app.py — Gradio 멀티모달 챗 UI

`python m05_gradio_app.py` → 로컬 7860 포트에 챗 UI 가 뜸.
브라우저에서 이미지 드래그 + 텍스트 입력으로 대화.

⚠ 강의 데모용. 같은 ChatInterface 패턴이 production gateway 에 그대로 쓰임.
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import gradio as gr

from _common import get_vlm, banner, llm_unavailable
from importlib import import_module
MultimodalChat = import_module("m04_multimodal_chat_memory").MultimodalChat


def main() -> None:
    banner("Gradio 멀티모달 챗 UI — http://localhost:7860")
    llm = get_vlm()
    if llm is None:
        llm_unavailable()
        return

    chat = MultimodalChat(llm)

    def respond(message, history):
        text = message.get("text", "") if isinstance(message, dict) else str(message)
        files = message.get("files", []) if isinstance(message, dict) else []
        image_path = files[0] if files else None
        return chat.send(text, image_path=image_path)

    demo = gr.ChatInterface(
        fn=respond,
        multimodal=True,
        type="messages",
        title="멀티모달 챗봇 (supp_05)",
        description="이미지를 올리고 질문해보세요. 후속 질문에 이미지는 재전송 안 해도 됩니다.",
    )
    demo.launch(server_name="127.0.0.1", server_port=7860, inbrowser=False, prevent_thread_lock=False)


if __name__ == "__main__":
    main()
