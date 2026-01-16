import re
import requests
from bs4 import BeautifulSoup
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers.openai_tools import JsonOutputToolsParser

# 1. 도구 정의
@tool
def get_word_length(word: str) -> int:
    """Returns the length of a word."""
    return len(word)

@tool
def naver_news_crawl(news_url: str) -> str:
    """Crawls a 네이버 (naver.com) news article and returns the body content."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(news_url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 네이버 뉴스 구조에 따른 선택자 처리
            title_element = soup.find("h2", id="title_area")
            content_element = soup.find("div", id="contents")
            
            title = title_element.get_text() if title_element else "제목을 찾을 수 없음"
            content = content_element.get_text() if content_element else "본문을 찾을 수 없음"
            
            cleaned_title = re.sub(r"\n{2,}", "\n", title).strip()
            cleaned_content = re.sub(r"\n{2,}", "\n", content).strip()
            
            return f"제목: {cleaned_title}\n\n본문: {cleaned_content}"
        else:
            return f"HTTP 요청 실패. 응답 코드: {response.status_code}"
    except Exception as e:
        return f"에러 발생: {str(e)}"

tools = [naver_news_crawl, get_word_length]

# 2. 도구 호출 실행 함수
def execute_tool_calls(tool_call_results):
    """
    도구 호출 결과 리스트를 받아 실제 함수를 실행합니다.
    """
    if not tool_call_results:
        print("도구 호출이 발생하지 않았습니다.")
        return

    for tool_call in tool_call_results:
        # JsonOutputToolsParser는 'type'과 'args' 키를 가진 딕셔너리를 반환합니다.
        tool_name = tool_call["type"]
        tool_args = tool_call["args"]

        # 이름에 맞는 도구 찾기
        matching_tool = next((t for t in tools if t.name == tool_name), None)

        if matching_tool:
            print(f"\n[실행도구] {tool_name}")
            print(f"[전달인자] {tool_args}")
            result = matching_tool.invoke(tool_args)
            print("-" * 30)
            print(f"[실행결과]\n{result}")
            print("-" * 30)
        else:
            print(f"경고: {tool_name} 도구를 찾을 수 없습니다.")

# 3. 모델 설정 (Ollama)
# 도구 호출 기능이 탑재된 mistral 모델 사용
llm = ChatOllama(model="mistral:latest", temperature=0)
llm_with_tools = llm.bind_tools(tools)

# 4. 체인 구성 (Bind -> Parser -> Exec)
# JsonOutputToolsParser는 LLM의 출력을 도구 호출용 JSON 구조로 파싱합니다.
chain = llm_with_tools | JsonOutputToolsParser() | execute_tool_calls

# 5. 실행
if __name__ == "__main__":
    news_url = "https://n.news.naver.com/article/607/0000002452"
    query = f"다음 뉴스 기사 내용을 크롤링해줘: {news_url}"
    
    print(f"질문: {query}")
    chain.invoke(query)