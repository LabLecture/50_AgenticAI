from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import requests
import os
from datetime import datetime
load_dotenv()

# ChatOpenAI 모델 초기화
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.9, max_tokens=1000)

# DALL-E 이미지 생성을 위한 프롬프트 템플릿 정의
prompt = PromptTemplate.from_template(
    "Generate a detailed IMAGE GENERATION prompt for DALL-E based on the following description. "
    "Return only the prompt, no intro, no explanation, no chatty, no markdown, no code block, no nothing. Just the prompt"
    "Output should be less than 1000 characters. Write in English only."
    "Image Description: \n{image_desc}",
)

# 프롬프트, LLM, 출력 파서를 연결하는 체인 생성
chain = prompt | llm | StrOutputParser()

# 체인 실행
image_prompt = chain.invoke(
    {"image_desc": "스마트폰을 바라보는 사람들을 풍자한 neo-classicism painting"}
)

# 이미지 프롬프트 출력
print(image_prompt)

# DALL-E API 래퍼 가져오기
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper

# DALL-E API 래퍼 초기화
# model: 사용할 DALL-E 모델 버전
# size: 생성할 이미지 크기
# quality: 이미지 품질
# n: 생성할 이미지 수
dalle = DallEAPIWrapper(model="dall-e-3", size="1024x1024", quality="standard", n=1)

# 질문
query = "스마트폰을 바라보는 사람들을 풍자한 neo-classicism painting"

# 이미지 생성 및 URL 받기
# chain.invoke()를 사용하여 이미지 설명을 DALL-E 프롬프트로 변환
# dalle.run()을 사용하여 실제 이미지 생성
image_url = dalle.run(chain.invoke({"image_desc": query}))

# 이미지를 저장할 디렉토리 생성
output_dir = "generated_images"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 현재 시간을 파일명에 포함하여 고유한 파일명 생성
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
image_filename = f"{output_dir}/dalle_image_{timestamp}.png"

# 이미지 URL에서 이미지 다운로드 및 저장
response = requests.get(image_url)
if response.status_code == 200:
    with open(image_filename, 'wb') as f:
        f.write(response.content)
    print(f"이미지가 성공적으로 저장되었습니다: {image_filename}")
else:
    print("이미지 다운로드에 실패했습니다.")
