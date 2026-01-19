#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from langgraph.prebuilt import ToolNode, tools_condition

# function_call_tool.py에서 tools를 가져온다고 가정합니다.
from function_call_tool import tools 

# 1. 그래프 상태(State) 정의
class State(TypedDict):
    # add_messages는 기존 메시지 리스트에 새 메시지를 누적(append)해주는 역할을 합니다.
    messages: Annotated[list, add_messages]

# 2. LLM 초기화 및 도구 바인딩
# llm = ChatOllama(model="mistral:latest")
llm = ChatOllama(model="qwen3:8b")
llm_with_tools = llm.bind_tools(tools)

# 3. 노드 함수 정의
def chatbot(state: State):
    """LLM이 상황을 판단하여 도구를 호출하거나 응답합니다."""
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

# 4. 그래프 구축
builder = StateGraph(State)

# 노드 추가
builder.add_node("chatbot", chatbot)
# ToolNode는 도구 실행을 자동화해주는 특수 노드입니다.
builder.add_node("tools", ToolNode(tools))

# 엣지(흐름) 연결
builder.add_edge(START, "chatbot")

# tools_condition: LLM 응답에 tool_calls가 있으면 "tools" 노드로, 없으면 종료(END)로 보냅니다.
builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)

# 도구 실행 후 다시 챗봇에게 돌아가 최종 답변을 생성하게 합니다.
builder.add_edge("tools", "chatbot")

# 컴파일
graph = builder.compile()


# In[6]:


# from IPython.display import Image, display
# display(Image(graph.get_graph().draw_mermaid_png()))


# In[7]:


# 5. 실행 테스트
QUESTION_LIST = [
    "주문 조회해줘",
    "내 등급 조회",
    "스트라이프 셔츠 주문한거 언제와",
    "내 등급이랑 주문정보 알려줘", # multi tool use
    "한국의 수도가 어디야"
]

def run_langgraph_example():
    for q in QUESTION_LIST:
        print(f"Q: {q}")
        
        # 그래프 실행 (초기 메시지 주입)
        initial_state = {"messages": [HumanMessage(content=q)]}
        
        # stream 모드를 사용하면 내부 과정을 실시간으로 볼 수 있습니다.
        # 여기서는 최종 결과만 출력합니다.
        final_state = graph.invoke(initial_state)
        
        # 마지막 메시지가 AI의 최종 답변입니다.
        print(f"A : {final_state['messages'][-1].content}\n")
        print("-" * 50)


# In[8]:


if __name__ == "__main__":
    run_langgraph_example()


# In[ ]:




