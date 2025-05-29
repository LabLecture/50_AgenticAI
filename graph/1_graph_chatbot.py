from dotenv import load_dotenv
load_dotenv()

from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


# State 정의
class State(TypedDict):
    messages: Annotated[list, add_messages]


# from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama

# LLM 초기화
llm = ChatOllama(model="mistral:latest", base_url="http://61.108.166.16:11434")

question = "서울의 유명한 맛집 TOP 10 추천해줘"
llm.invoke(question)

# 챗봇 함수 정의
def chatbot(state: State):
    # 메시지 호출 및 반환
    return {"messages": [llm.invoke(state["messages"])]}

# 그래프 생성 및 노드를 추가
from langgraph.graph import StateGraph, START, END

graph_builder = StateGraph(State)           # 상태 그래프 초기화
graph_builder.add_node("chatbot", chatbot)  # 노드 추가
graph_builder.add_edge(START, "chatbot")    # 시작 노드에서 챗봇 노드로의 엣지 추가
graph_builder.add_edge("chatbot", END)      # 그래프에 엣지 추가
graph = graph_builder.compile()             # 그래프 컴파일

# 그래프 시각화
from IPython.display import Image, display
display(Image(graph.get_graph().draw_mermaid_png()))

question = "서울의 유명한 맛집 TOP 10 추천해줘"

# 그래프 이벤트 스트리밍
for event in graph.stream({"messages": [("user", question)]}):
    # 이벤트 값 출력
    for value in event.values():
        print("Assistant:", value["messages"][-1].content)
