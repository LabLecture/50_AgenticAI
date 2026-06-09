"""
m06_multimodal_rag.py — CLIP 기반 멀티모달 RAG

(1) sample_images/ 의 이미지들을 CLIP 으로 임베딩
(2) 텍스트 질문을 같은 CLIP 으로 임베딩
(3) 코사인 유사도 Top-K 이미지 검색
(4) 검색된 이미지를 VLM 에 넣어 답변 생성
"""
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import numpy as np
import torch
from PIL import Image

from _assets import ensure_assets
from _common import get_vlm, banner, llm_unavailable

# 같은 디렉토리의 m03 import (앞이 숫자라 직접 import 가능)
from importlib import import_module
ask_about_image = import_module("m03_single_image_call").ask_about_image


def main() -> None:
    banner("멀티모달 RAG — CLIP 으로 텍스트 → 이미지 검색 → VLM 답변")

    assets = ensure_assets()
    library = [assets["chart"], assets["scene"], assets["receipt"]]

    print("\n[Step 1] CLIP 모델 로드 (ViT-B-32, ~150MB, 최초 호출 시 다운로드)")
    import open_clip
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="laion2b_s34b_b79k"
    )
    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    model.eval()

    def embed_image(path):
        img = preprocess(Image.open(path).convert("RGB")).unsqueeze(0)
        with torch.no_grad():
            v = model.encode_image(img)[0].numpy()
        return v / np.linalg.norm(v)

    def embed_text(text):
        tok = tokenizer([text])
        with torch.no_grad():
            v = model.encode_text(tok)[0].numpy()
        return v / np.linalg.norm(v)

    print("[Step 2] 이미지 라이브러리 임베딩")
    image_vecs = np.stack([embed_image(p) for p in library])

    queries = [
        ("a bar chart",        "이 차트가 보여주는 정보는?"),
        ("colorful shapes",    "보이는 도형들을 정리해."),
        ("a paper receipt",    "이 영수증의 TOTAL 은?"),
    ]

    llm = get_vlm()
    if llm is None:
        llm_unavailable()
        return

    for clip_q, vlm_q in queries:
        print("\n" + "─" * 70)
        print(f"🔍 CLIP query: {clip_q!r}")
        q_vec = embed_text(clip_q)
        sims = image_vecs @ q_vec
        ranked = sorted(zip(sims, library), reverse=True)
        for sim, path in ranked:
            from pathlib import Path
            print(f"   sim={float(sim):+.3f}  {Path(path).name}")

        top_img = ranked[0][1]
        print(f"   → Top-1 → VLM 질문: {vlm_q!r}")
        try:
            ans = ask_about_image(llm, top_img, vlm_q)
            print(f"   💬 {ans.strip()[:200]}")
        except Exception as e:
            print(f"   ⚠ {type(e).__name__}: {str(e)[:150]}")


if __name__ == "__main__":
    main()
