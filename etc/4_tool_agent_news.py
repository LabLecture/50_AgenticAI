import re
import requests
from bs4 import BeautifulSoup
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.agents import create_agent

# 1. 도구(Tools) 정의
@tool
def get_word_length(text: str) -> int:
    """텍스트의 글자 수(길이)를 반환합니다."""
    return len(text)

@tool
def naver_news_crawl(news_url: str) -> str:
    """네이버 뉴스 URL을 입력받아 제목과 본문 내용을 크롤링하여 반환합니다."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(news_url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 네이버 뉴스 구조에 맞춘 선택자 (구조 변경 시 수정 필요)
            title_element = soup.find("h2", id="title_area")
            content_element = soup.find("div", id="contents") or soup.find("article", id="dic_area")
            
            title = title_element.get_text().strip() if title_element else "제목 없음"
            content = content_element.get_text().strip() if content_element else "본문 없음"
            
            # 불필요한 공백 및 줄바꿈 정리
            cleaned_content = re.sub(r"\n{2,}", "\n", content)
            return f"제목: {title}\n본문: {cleaned_content}"
        else:
            return f"HTTP 요청 실패 (코드: {response.status_code})"
    except Exception as e:
        return f"에러 발생: {str(e)}"

# 사용할 도구 리스트
tools = [naver_news_crawl, get_word_length]

# 2. LLM 및 에이전트 설정
# 도구 호출 기능이 안정적인 mistral 모델을 사용합니다.
llm = ChatOllama(model="mistral:latest", temperature=0)

# 3. 에이전트 생성 (제시해주신 예제 패턴 적용)
news_agent = create_agent(
    model=llm, # 혹은 바인딩된 llm
    tools=tools,
    system_prompt=SystemMessage(
        content="당신은 뉴스 분석 전문가입니다. 제공된 도구를 사용해 뉴스를 크롤링하고, "
                "그 내용을 요약한 뒤 원문과 요약문의 글자 수를 비교하여 보고하세요. "
                "모든 답변은 한국어로 작성합니다."
    )
)

# 4. 에이전트 실행
if __name__ == "__main__":
    news_url = "https://n.news.naver.com/article/607/0000002452"
    
    # 예제와 동일하게 {"messages": [HumanMessage(...)]} 구조로 호출합니다.
    result = news_agent.invoke(
        {
            "messages": [
                HumanMessage(content=f"이 뉴스 기사를 요약하고 요약한 내용과 글자수를 알려줘: {news_url}")
            ]
        }
    )

    # 결과 출력
    # create_agent의 반환 방식에 따라 result["messages"][-1].content 등을 확인합니다.
    print("\n" + "="*50)
    print(result)