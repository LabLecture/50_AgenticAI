# 참고자료 
 - Human-in-the-Loop : https://wikidocs.net/318934 
 - Google ADK : 원래 title은 Google ADK (Session/Memory, HITL) 임
    - https://wikidocs.net/286690 (stop됨:25'12)
    - https://davinci-ai.tistory.com/73 : 문답식으로 간단히 생성. (uv로 install)
    - https://google.github.io/adk-docs/get-started/python/#installation (pip install)
    - https://aiheroes.ai/community/338 : Google ADK 기반 멀티 에이전트 마케팅 시스템 구축하기 (소스식)    

# Google ADK
 1. 정의 : 멀티 에이전트 기반의 AI 애플리케이션을 구축하기 위한 개발자 도구 모음(toolkit)
 2. 특징 
    1. 배포에 구애받지 않으며, 다른 프레임워크와 호환되도록 제작
      - Python, Java(Maven, Gradle)
        - 메이븐(Apache Maven)은 개발자로 하여금 자바용 프로젝트 관리를 쉽게 도와주는 빌드 툴. elipse내 
        - Gradle은 Groovy 또는 Kotlin 기반의 오픈 소스 빌드 자동화 도구    
## 실습 1 : quickstart (google.github.io/adk-docs)
 - https://google.github.io/adk-docs/get-started/python/#installation (pip install)   
 - adk create my_agent .. 
    PS C:\git\king\50_AgenticAI\adk> py -3.12 -m venv venv
    PS C:\git\king\50_AgenticAI\adk> .\venv\Scripts\activate
    (venv) PS C:\git\king\50_AgenticAI\adk> pip install google-adk
    (venv) PS C:\git\king\50_AgenticAI\adk> adk create adk01_my_agent
    Choose a model for the root agent:
    1. gemini-2.5-flash
    2. Other models (fill later)
    Choose model (1, 2): 1
    1. Google AI
    2. Vertex AI
    Choose a backend (1, 2): 1

    Don't have API Key? Create one in AI Studio: https://aistudio.google.com/apikey

    Enter Google API key: AIzaSyBlROdxrXXXXXXXXXXXXXX-2fgJ62yGU

    Agent created in C:\git\king\50_AgenticAI\adk\adk01_my_agent:
    - .env
    - __init__.py
    - agent.py

    (venv) PS C:\git\king\50_AgenticAI\adk> adk run adk01_my_agent
    Log setup complete: C:\Users\INTERR~1\AppData\Local\Temp\agents_log\agent.20260317_145558.log
    To access latest log: tail -F C:\Users\INTERR~1\AppData\Local\Temp\agents_log\agent.20260317_145558.log
    C:\git\king\50_AgenticAI\adk\venv\Lib\site-packages\google\adk\cli\cli.py:204: UserWarning: [EXPERIMENTAL] InMemoryCredentialService: This feature is experimental and may change or be removed in future versions without notice. It may introduce breaking changes at any time.
    credential_service = InMemoryCredentialService()
    C:\git\king\50_AgenticAI\adk\venv\Lib\site-packages\google\adk\auth\credential_service\in_memory_credential_service.py:33: UserWarning: [EXPERIMENTAL] BaseCredentialService: This feature is experimental and may change or be removed in future versions without notice. It may introduce breaking changes at any time.
    super().__init__()
    Running agent root_agent, type exit to exit.
    [user]: what can you do?
    [root_agent]: I can tell you the current time in a specified city using the `get_current_time` function.
    [user]: what time it is in Seoul?
    [root_agent]: The time in Seoul is 10:30 AM.
    [user]: 
    Aborted!

    (venv) PS C:\git\king\50_AgenticAI\adk> adk web --port 8000
    ... 
    INFO:     Started server process [34532]
    INFO:     Waiting for application startup.

    +-----------------------------------------------------------------------------+
    | ADK Web Server started                                                      |
    |                                                                             |
    | For local testing, access at http://127.0.0.1:8000.                         |
    +-----------------------------------------------------------------------------+

    INFO:     Application startup complete.
    INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)

## 실습 2 : simple multi agent (google.github.io/adk-docs)[미완]
 - https://google.github.io/adk-docs/get-started/quickstart/#run-your-agent
 - adk create adk02_multi_tool_agent...
    (venv) PS C:\git\king\50_AgenticAI\adk> adk create adk02_multi_tool_agent
    ...
    (venv) PS C:\git\king\50_AgenticAI\adk> adk run adk02_multi_tool_agent
    (venv) PS C:\git\king\50_AgenticAI\adk> adk web
    You exceeded your current quota... 

## 실습 3 : simple multi agent (google.github.io/adk-docs) & OpenRouter
 - (venv) PS C:\git\king\50_AgenticAI\adk> pip install litellm>=1.75.5
 - (venv) PS C:\git\king\50_AgenticAI\adk> pip install "google-adk[extensions]" 
 - .env 수정 
 - agent.py 수정 
    from google.adk.models.lite_llm import LiteLlm
    root_agent = Agent(
        name="weather_time_agent",
        model=LiteLlm(model="openrouter/openai/gpt-oss-20b:free"),

## 실습 4 : Google ADK 기반 멀티 에이전트 마케팅 시스템 구축 & OpenRouter
 - https://aiheroes.ai/community/338


## 실습 5 : 숙제형 실습 [학습지_수업진도체크]