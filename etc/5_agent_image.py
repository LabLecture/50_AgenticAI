import os
from datetime import datetime
from PIL import Image
from dotenv import load_dotenv

# Hugging Face InferenceClient 임포트
from huggingface_hub import InferenceClient

# LangChain 관련 임포트
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from langchain.agents import create_agent # 사용자 환경에서 성공한 방식

load_dotenv()

# --- [1. 이미지 생성 도구 정의: InferenceClient 활용] ---
@tool
def generate_image_tool(prompt: str) -> str:
    """
    Generates an image using Hugging Face InferenceClient.
    The 'prompt' should be a detailed description in English.
    """
    try:
        # HF_TOKEN은 .env 파일에 저장되어 있어야 합니다.
        client = InferenceClient(
            provider="nscale",
            api_key=os.environ.get("HUGGINGFACEHUB_API_TOKEN"),
        )

        # 이미지 생성 (PIL.Image 객체 반환)
        image = client.text_to_image(
            prompt,
            model="stabilityai/stable-diffusion-xl-base-1.0",
        )

        # 이미지 저장 경로 설정
        output_dir = "generated_images"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"{output_dir}/hf_client_{timestamp}.png"

        # PIL 이미지 저장
        image.save(file_path)
        
        return f"Image successfully generated and saved at: {file_path}"

    except Exception as e:
        return f"Error during image generation: {str(e)}"

# 도구 리스트
tools = [generate_image_tool]

# --- [2. 로컬 LLM 설정: Ollama] ---
llm = ChatOllama(model="mistral:latest", temperature=0)

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