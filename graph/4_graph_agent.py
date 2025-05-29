from dotenv import load_dotenv
load_dotenv()

# ### 1. TavilySearchResults 검색 API 도구 사용
from langchain_tavily import TavilySearch

tool = TavilySearch(max_results=3)      # 검색 도구 생성
tools = [tool]                          # 도구 목록에 추가

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

# State 정의
class State(TypedDict):
    messages: Annotated[list, add_messages]

from langchain_openai import ChatOpenAI

# LLM 초기화
llm = ChatOpenAI(model="gpt-4o-mini")
# LLM 에 도구 바인딩
llm_with_tools = llm.bind_tools(tools)      # ChatOpenAI 에만 적용됨.


# 노드 함수 정의
def chatbot(state: State):
    answer = llm_with_tools.invoke(state["messages"])
    return {"messages": [answer]}  # 자동으로 add_messages 적용


# 그래프 생성 및 노드를 추가
from langgraph.graph import StateGraph
graph_builder = StateGraph(State)           # 상태 그래프 초기화
graph_builder.add_node("chatbot", chatbot)  # 노드 추가

import json
from langchain_core.messages import ToolMessage

class BasicToolNode:
    """Run tools requested in the last AIMessage node"""

    def __init__(self, tools: list) -> None:
        self.tools_list = {tool.name: tool for tool in tools}           # 도구 리스트

    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):  # 메시지가 존재할 경우 가장 최근 메시지 1개 추출
            message = messages[-1]
        else:
            raise ValueError("No message found in input")

        # 도구 호출 결과
        outputs = []
        for tool_call in message.tool_calls:
            # 도구 호출 후 결과 저장
            tool_result = self.tools_list[tool_call["name"]].invoke(tool_call["args"])
            outputs.append(                     # 도구 호출 결과를 메시지로 저장
                ToolMessage(
                    content=json.dumps(
                        tool_result, ensure_ascii=False
                    ),  # 도구 호출 결과를 문자열로 변환
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}

tool_node = BasicToolNode(tools=[tool])     # 도구 노드 생성
graph_builder.add_node("tools", tool_node)  # 그래프에 도구 노드 추가


from langgraph.graph import START, END

# route_tools라는 라우터 함수를 정의하여 챗봇의 출력에서 tool_calls를 확인
def route_tools(
    state: State,
):
    if messages := state.get("messages", []):
        ai_message = messages[-1]   # 가장 최근 메시지를 가져옴
    else:
        # 입력 상태에 메시지가 없는 경우 예외 발생
        raise ValueError(f"No messages found in input state to tool_edge: {state}")

    # AI 메시지에 도구 호출이 있는 경우 "tools" 반환
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"  # 도구 호출이 있는 경우 "tools" 반환
    return END          # 도구 호출이 없는 경우 END 반환    


# tools_condition 함수는 챗봇이 도구 사용을 요청하면 "tools"를 반환하고, 직접 응답이 가능한 경우 "END"를 반환
graph_builder.add_conditional_edges(
    source="chatbot",
    path=route_tools,
    # route_tools 의 반환값이 "tools" 인 경우 "tools" 노드로, 그렇지 않으면 END 노드로 라우팅
    path_map={"tools": "tools", END: END},
)

graph_builder.add_edge("tools", "chatbot")  # tools > chatbot
graph_builder.add_edge(START, "chatbot")    # START > chatbot
graph = graph_builder.compile()             # 그래프 컴파일

question = "한국의 다음 대통령 선거"

for event in graph.stream({"messages": [("user", question)]}):
    for key, value in event.items():
        print(f"\n==============\nSTEP: {key}\n==============\n")
        # display_message_tree(value["messages"][-1])
        print(value["messages"][-1])
        # event["messages"][-1].pretty_print()