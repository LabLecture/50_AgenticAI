# ※ [메모 2026-10] 이미지 생성 API 정책 변경으로 현재 이 실습은 진행이 어렵습니다.
#    - DALL-E(dall-e-3) 서비스 종료, Hugging Face Inference Providers 정책 변경
#    - OpenRouter 이미지 모델은 키 잔액 $1 이상 필요
#    코드는 참고용으로 원본 그대로 둡니다.
import os
from datetime import datetime
from PIL import Image
from dotenv import load_dotenv

import base64
# [참고] 기존: Hugging Face InferenceClient (HF 정책 변경으로 OpenRouter 이미지 모델로 교체)
# from huggingface_hub import InferenceClient
from openai import OpenAI

# LangChain 관련 임포트
# from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from langchain.agents import create_agent # 사용자 환경에서 성공한 방식

load_dotenv()

# [참고] 기존: Hugging Face InferenceClient 버전
# # --- [1. 이미지 생성 도구 정의: InferenceClient 활용] ---
# @tool
# def generate_image_tool(prompt: str) -> str:
#     """
#     Generates an image using Hugging Face InferenceClient.
#     The 'prompt' should be a detailed description in English.
#     """
#     try:
#         # HF_TOKEN은 .env 파일에 저장되어 있어야 합니다.
#         client = InferenceClient(
#             provider="nscale",
#             api_key=os.environ.get("HF_TOKEN"),
#         )
#
#         # 이미지 생성 (PIL.Image 객체 반환)
#         image = client.text_to_image(
#             prompt,
#             # SDXL 은 nscale provider 미지원 → nscale 에서 live 인 FLUX.1-schnell 사용
#             model="black-forest-labs/FLUX.1-schnell",
#         )
#
#         # 이미지 저장 경로 설정
#         output_dir = "generated_images"
#         os.makedirs(output_dir, exist_ok=True)
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         file_path = f"{output_dir}/hf_client_{timestamp}.png"
#
#         # PIL 이미지 저장
#         image.save(file_path)
#
#         return f"Image successfully generated and saved at: {file_path}"
#
#     except Exception as e:
#         return f"Error during image generation: {str(e)}"

# --- [1. 이미지 생성 도구 정의: OpenRouter 이미지 모델] ---
# 이미지 모델은 OPENROUTER_IMAGE_MODEL 로 변경 가능 (OpenRouter 키 잔액 $1 이상 필요)
IMAGE_MODEL = os.getenv("OPENROUTER_IMAGE_MODEL") or "google/gemini-2.5-flash-image"

@tool
def generate_image_tool(prompt: str) -> str:
    """
    Generates an image using an OpenRouter image model.
    The 'prompt' should be a detailed description in English.
    """
    try:
        client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )
        # modalities 에 image 를 넣으면 응답 message.images 에 data URL(base64) 로 이미지가 옴
        resp = client.chat.completions.create(
            model=IMAGE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            extra_body={"modalities": ["image", "text"]},
        )
        msg = resp.choices[0].message
        images = getattr(msg, "images", None) or (msg.model_extra or {}).get("images")
        if not images:
            return f"No image returned: {msg.content}"
        data_url = images[0]["image_url"]["url"]

        # 이미지 저장 경로 설정
        output_dir = "generated_images"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"{output_dir}/openrouter_{timestamp}.png"
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(data_url.split(",", 1)[1]))

        return f"Image successfully generated and saved at: {file_path}"

    except Exception as e:
        return f"Error during image generation: {str(e)}"

# 도구 리스트
tools = [generate_image_tool]

# --- [2. LLM 설정: OpenRouter] ---
# [참고] 기존: llm = ChatOllama(model="mistral:latest", temperature=0)
# OpenRouter Gemma 4 26B A4B (OPENROUTER_MODEL 로 변경 가능)
llm = ChatOpenAI(
    model=os.getenv("OPENROUTER_MODEL") or "google/gemma-4-26b-a4b-it",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0,
)

# --- [3. 에이전트 생성 (사용자 방식 유지)] ---
image_agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=SystemMessage(
        content=(
            "You are an AI that creates images. "
            "When a user asks for a picture, use the 'generate_image_tool'. "
            "IMPORTANT: Always translate the user's request into a detailed "
            "English prompt for the tool. Don't say you can't do it; use the tool."
        )
    )
)

# --- [4. 실행] ---
query = "스마트폰을 바라보는 사람들을 풍자한 신고전주의 화풍의 그림을 그려줘"

print("--- 에이전트 가동 중 ---")
result = image_agent.invoke(
    {"messages": [HumanMessage(content=query)]}
)

# 결과 출력
print("\n--- 최종 답변 ---")
print(result["messages"][-1].content)