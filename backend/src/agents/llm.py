import os
from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
# [참고] 기존: from langchain_ollama import ChatOllama
from typing import Optional

# [참고] 기존: from src.config import (REASONING_*, BASIC_*, VL_*) → OpenRouter 로 통일하며 제거
from src.config.agents import LLMType

# OpenRouter 설정 (OPENROUTER_API_KEY 필수, OPENROUTER_MODEL 선택)
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
# [참고] 기존 기본값 openai/gpt-oss-20b 는 가짜 tool_call(repo_browser.write 등)·빈 JSON 응답이 잦아 Gemma 4 로 변경
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemma-4-26b-a4b-it")


def create_openai_llm(
    model: str,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0.0,
    **kwargs,
) -> ChatOpenAI:
    """
    Create a ChatOpenAI instance with the specified configuration
    """
    # Only include base_url in the arguments if it's not None or empty
    llm_kwargs = {"model": model, "temperature": temperature, **kwargs}

    if base_url:  # This will handle None or empty string
        llm_kwargs["base_url"] = base_url

    if api_key:  # This will handle None or empty string
        llm_kwargs["api_key"] = api_key

    return ChatOpenAI(**llm_kwargs)


def create_deepseek_llm(
    model: str,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0.0,
    **kwargs,
) -> ChatDeepSeek:
    """
    Create a ChatDeepSeek instance with the specified configuration
    """
    # Only include base_url in the arguments if it's not None or empty
    llm_kwargs = {"model": model, "temperature": temperature, **kwargs}

    if base_url:  # This will handle None or empty string
        llm_kwargs["api_base"] = base_url

    if api_key:  # This will handle None or empty string
        llm_kwargs["api_key"] = api_key

    return ChatDeepSeek(**llm_kwargs)


# Cache for LLM instances
_llm_cache: dict[LLMType, ChatOpenAI | ChatDeepSeek] = {}


def get_llm_by_type(llm_type: LLMType) -> ChatOpenAI | ChatDeepSeek:
    """
    Get LLM instance by type. Returns cached instance if available.
    """
    if llm_type in _llm_cache:
        return _llm_cache[llm_type]
    if llm_type not in ("basic", "reasoning", "vision", "supervisor"):
        raise ValueError(f"Unknown LLM type: {llm_type}")
    # 모든 타입(basic / reasoning / vision / supervisor)을 OpenRouter Gemma 4 26B A4B 로 통일
    # (Gemma 4 는 이미지 입력도 지원 → vision 도 같은 모델 사용)
    # supervisor(planner 포함)는 JSON 응답 강제
    extra = {"model_kwargs": {"response_format": {"type": "json_object"}}} if llm_type == "supervisor" else {}
    llm = create_openai_llm(
        model=OPENROUTER_MODEL,
        base_url=OPENROUTER_BASE_URL,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        **extra,
    )

    # [참고] 기존: Ollama / BASIC_* (OpenAI 호환) 분기
    # # model_name = "qwen2.5:14b"      # 
    # # model_name = "cogito:14b"       # user_class_tool start user_name: 사형로, user_school: 찴분리당, user_grade: 6
    # # model_name = "deepseek-r1:14b"  # English
    # # model_name = "mistral:latest"   # An error occurred: 'next'
    # # model_name = "mistral-nemo:12b" # An error occurred: 'next'
    # # .env 의 OLLAMA_MODEL / OLLAMA_BASE_URL 우선, 없으면 기존 값
    # model_name = os.getenv("OLLAMA_MODEL", "qwen3:8b")         # 서버 멈춤 An error occurred: 'next'
    # # model_name = "mistral-small:latest" 
    # base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    # if BASIC_BASE_URL:
    #     # .env 에 BASIC_BASE_URL 이 있으면 OpenAI 호환 API(OpenRouter 등) 사용, supervisor 는 JSON 강제
    #     extra = {"model_kwargs": {"response_format": {"type": "json_object"}}} if llm_type == "supervisor" else {}
    #     llm = create_openai_llm(model=BASIC_MODEL, base_url=BASIC_BASE_URL, api_key=BASIC_API_KEY, **extra)
    # elif llm_type == "reasoning":
    #     # llm = create_deepseek_llm(
    #     #     model=REASONING_MODEL,
    #     #     base_url=REASONING_BASE_URL,
    #     #     api_key=REASONING_API_KEY,
    #     # )     
    #     # llm = ChatOllama(model=model_name, temperature=0)
    #     llm = ChatOllama(model=model_name, temperature=0, base_url = base_url)
    #     # print(type(llm))
    # elif llm_type == "supervisor":
    #     # llm = ChatOllama(model=model_name, temperature=0, format="json")
    #     llm = ChatOllama(model=model_name, temperature=0, format="json", base_url = base_url)
    # elif llm_type == "basic":
    #     # llm = ChatOllama(model=model_name, temperature=0)
    #     llm = ChatOllama(model=model_name, temperature=0, base_url = base_url)
    #     # llm = ChatOllama(model="qwq:latest", temperature=0)
    #     # print(type(llm))
    #     # llm = create_openai_llm(
    #     #     model=BASIC_MODEL,
    #     #     base_url=BASIC_BASE_URL,
    #     #     api_key=BASIC_API_KEY,
    #     # )
    # elif llm_type == "vision":
    #     # llm = create_openai_llm(
    #     #     model=VL_MODEL,
    #     #     base_url=VL_BASE_URL,
    #     #     api_key=VL_API_KEY,
    #     # )
    #     llm = ChatOllama(model=model_name, temperature=0, base_url = base_url)
    #     # llm = ChatOllama(model="mistral-small:latest", temperature=0, base_url = "http://192.168.1.203:11434")
    # else:
    #     raise ValueError(f"Unknown LLM type: {llm_type}")

    _llm_cache[llm_type] = llm
    return llm


# Initialize LLMs for different purposes - now these will be cached
reasoning_llm = get_llm_by_type("reasoning")
basic_llm = get_llm_by_type("basic")
vl_llm = get_llm_by_type("vision")


if __name__ == "__main__":
    # stream = reasoning_llm.stream("what is mcp?")
    # full_response = ""
    # for chunk in stream:
    #     full_response += chunk.content
    print("__main__")

    # basic_llm.invoke("Hello")
    # vl_llm.invoke("Hello")
