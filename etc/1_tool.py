from langchain_experimental.tools import PythonREPLTool
import os
from dotenv import load_dotenv
load_dotenv()
# 파이썬 코드를 실행하는 도구를 생성합니다.
python_tool = PythonREPLTool()

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda


# 파이썬 코드를 실행하고 중간 과정을 출력하고 도구 실행 결과를 반환하는 함수
def print_and_execute(code, debug=True):
    if debug:
        print("CODE:")
        print(code)
    return python_tool.invoke(code)


# 파이썬 코드를 작성하도록 요청하는 프롬프트
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are Raymond Hetting, an expert python programmer, well versed in meta-programming and elegant, concise and short but well documented code. You follow the PEP8 style guide. "
            "Return only the code, no intro, no explanation, no chatty, no markdown, no code block, no nothing. Just the code.",
        ),
        ("human", "{input}"),
    ]
)
# LLM 모델 생성
# [참고] 기존: llm = ChatOpenAI(model="gpt-4o", temperature=0)
# OpenRouter Gemma 4 26B A4B 사용 (OPENROUTER_API_KEY 필요)
llm = ChatOpenAI(
    model=os.getenv("OPENROUTER_MODEL", "google/gemma-4-26b-a4b-it"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0,
)

# 프롬프트와 LLM 모델을 사용하여 체인 생성
chain = prompt | llm | StrOutputParser() | RunnableLambda(print_and_execute)

# 결과 출력
print(chain.invoke("로또 번호 생성기를 출력하는 코드를 작성하세요."))
