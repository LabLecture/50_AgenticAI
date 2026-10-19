import logging
import os
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from src.config import TAVILY_MAX_RESULTS
from .decorators import create_logged_tool

logger = logging.getLogger(__name__)

if os.getenv("TAVILY_API_KEY"):
    # Initialize Tavily search tool with logging
    LoggedTavilySearch = create_logged_tool(TavilySearchResults)
    tavily_tool = LoggedTavilySearch(name="tavily_search", max_results=TAVILY_MAX_RESULTS)
else:
    # 키가 없으면 TavilySearchResults 생성 시 검증 오류로 서버가 죽음 → 안내 메시지만 돌려주는 스텁 사용
    logger.warning("TAVILY_API_KEY 미설정 → 웹검색 비활성화")

    @tool
    def tavily_tool(query: str) -> list:
        """웹검색 (TAVILY_API_KEY 미설정 시 비활성화)"""
        return [{"title": "검색 키 미설정", "content": "TAVILY_API_KEY 가 없어 웹검색을 건너뜁니다."}]
