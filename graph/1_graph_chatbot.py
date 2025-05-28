#!/usr/bin/env python
# coding: utf-8

# In[1]:


# API 키를 환경변수로 관리하기 위한 설정 파일
from dotenv import load_dotenv

# API 키 정보 로드
load_dotenv()
# https://wikidocs.net/264614 

# In[2]:


from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


# State 정의
class State(TypedDict):
    # list 타입에 add_messages 적용(list 에 message 추가)
    messages: Annotated[list, add_messages]

# In[3]:


# !pip install langchain-ollama

# In[4]:


# from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
# from langchain_ollama import ChatOllama

# LLM 초기화
# llm = ChatOpenAI(api_key="ollama", model="mistral:latest", base_url="http://61.108.166.16:11434")
# llm = ChatOpenAI(model="gpt-4o-mini")
# llm = ChatOllama(model="mistral:latest", base_url="http://61.108.166.16:11434")
llm = ChatOllama(model="mistral:latest", temperature=0, base_url = "http://192.168.1.203:11434")
# llm = ChatOllama(model="mistral:latest", base_url="http://ollama_dev:11434")


# In[5]:


question = "서울의 유명한 맛집 TOP 10 추천해줘"
llm.invoke(question)

# In[6]:


# 챗봇 함수 정의
def chatbot(state: State):
    # 메시지 호출 및 반환
    return {"messages": [llm.invoke(state["messages"])]}

# In[7]:


# 그래프 생성 및 노드를 추가
from langgraph.graph import StateGraph, START, END

# 상태 그래프 초기화
graph_builder = StateGraph(State)

# 노드 추가
graph_builder.add_node("chatbot", chatbot)

# In[8]:


# 시작 노드에서 챗봇 노드로의 엣지 추가
graph_builder.add_edge(START, "chatbot")
# 그래프에 엣지 추가
graph_builder.add_edge("chatbot", END)

# In[9]:


# 그래프 컴파일
graph = graph_builder.compile()

# In[10]:


from IPython.display import Image, display
display(Image(graph.get_graph().draw_mermaid_png()))

# In[11]:


question = "서울의 유명한 맛집 TOP 10 추천해줘"

# 그래프 이벤트 스트리밍
for event in graph.stream({"messages": [("user", question)]}):
    # 이벤트 값 출력
    for value in event.values():
        print("Assistant:", value["messages"][-1].content)

# In[ ]:



