from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import requests
import os
from datetime import datetime
load_dotenv()
import re
import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers.openai_tools import JsonOutputToolsParser

# 도구를 정의합니다.
@tool
def get_word_length(word: str) -> int:
    """Returns the length of a word."""
    return len(word)

@tool
def naver_news_crawl(news_url: str) -> str:
    """Crawls a 네이버 (naver.com) news article and returns the body content."""
    # HTTP GET 요청 보내기
    response = requests.get(news_url)

    # 요청이 성공했는지 확인
    if response.status_code == 200:
        # BeautifulSoup을 사용하여 HTML 파싱
        soup = BeautifulSoup(response.text, "html.parser")

        # 원하는 정보 추출
        title = soup.find("h2", id="title_area").get_text()
        content = soup.find("div", id="contents").get_text()
        cleaned_title = re.sub(r"\n{2,}", "\n", title)
        cleaned_content = re.sub(r"\n{2,}", "\n", content)
    else:
        print(f"HTTP 요청 실패. 응답 코드: {response.status_code}")

    return f"{cleaned_title}\n{cleaned_content}"


tools = [get_word_length, naver_news_crawl]

def execute_tool_calls(tool_call_results):
    """
    도구 호출 결과를 실행하는 함수

    :param tool_call_results: 도구 호출 결과 리스트
    :param tools: 사용 가능한 도구 리스트
    """
    # 도구 호출 결과 리스트를 순회합니다.
    for tool_call_result in tool_call_results:
        # 도구의 이름과 인자를 추출합니다.
        tool_name = tool_call_result["type"]
        tool_args = tool_call_result["args"]

        # 도구 이름과 일치하는 도구를 찾아 실행합니다.
        # next() 함수를 사용하여 일치하는 첫 번째 도구를 찾습니다.
        matching_tool = next((tool for tool in tools if tool.name == tool_name), None)

        if matching_tool:
            # 일치하는 도구를 찾았다면 해당 도구를 실행합니다.
            result = matching_tool.invoke(tool_args)
            # 실행 결과를 출력합니다.
            print(f"[실행도구] {tool_name}\n[실행결과] {result}")
        else:
            # 일치하는 도구를 찾지 못했다면 경고 메시지를 출력합니다.
            print(f"경고: {tool_name}에 해당하는 도구를 찾을 수 없습니다.")

# [참고] 기존: llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
# OpenRouter Gemma 4 26B A4B (OPENROUTER_MODEL 로 변경 가능)
llm = ChatOpenAI(
    model=os.getenv("OPENROUTER_MODEL") or "google/gemma-4-26b-a4b-it",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0,
)	# 모델 생성
llm_with_tools = llm.bind_tools(tools)		            # 도구 바인딩

news_url = "https://n.news.naver.com/article/607/0000002452"    

# bind_tools + Parser + Execution
# chain = llm_with_tools | JsonOutputToolsParser(tools=tools) | execute_tool_calls
# chain.invoke("뉴스 기사 내용을 크롤링해줘: "+news_url)

############## 여기까지 하고 작업 후 1차 실행
############## 다음(우측) 실행시 1차 실행 마지막 두줄 주석 후 실행

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent  # langchain 1.x: classic 패키지로 이동

# Agent프롬프트 생성
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are very powerful assistant, but don't know current events",
        ),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# Agent 생성
agent = create_tool_calling_agent(llm, tools, prompt)

# AgentExecutor 생성
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
)

result = agent_executor.invoke(
    {
        "input": "뉴스 기사를 요약해 주고 크롱링한 원문 기사 글자수와 요약한 글자수를 알려줘 : "+news_url
    }
)
print(result["output"])