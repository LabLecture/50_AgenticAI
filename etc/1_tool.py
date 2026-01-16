from langchain_core.runnables import ConfigurableField
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

# 1. 도구(Tools) 정의
@tool
def multiply(x: float, y: float) -> float:
    """x와 y를 곱합니다."""
    return x * y

@tool
def exponentiate(x: float, y: float) -> float:
    """x의 y승(거듭제곱)을 계산합니다."""
    return x**y

@tool
def add(x: float, y: float) -> float:
    """x와 y를 더합니다."""
    return x + y

# 도구 리스트 구성
tools = [multiply, exponentiate, add]

# 2. LLM 설정 (Ollama 사용)
# 기기 성능에 따라 mistral 대신 llama3 혹은 gemma를 사용할 수 있습니다.
llm = ChatOllama(model="mistral:latest", temperature=0).bind_tools(tools)

# 3. ConfigurableField 설정 (모델이나 설정을 동적으로 바꿀 수 있게 함)
llm_with_tools = llm.configurable_alternatives(
    ConfigurableField(id="llm"), 
    default_key="llm"
)

# 4. 실행 함수 정의
def run_math_example(query: str):
    print(f"\n[질문]: {query}")
    
    # 모델 호출 (invoke)
    # config를 통해 특정 설정을 전달할 수 있습니다.
    response = llm_with_tools.invoke(
        [HumanMessage(content=query)],
        config={"configurable": {"llm": "llm"}}
    )
    
    # 5. 결과 출력
    # 모델이 도구를 사용하기로 결정했다면 tool_calls에 정보가 담깁니다.
    if response.tool_calls:
        print(" AI가 도구 사용을 결정했습니다:")
        for tool_call in response.tool_calls:
            print(f" - 사용 도구: {tool_call['name']}")
            print(f" - 입력 파라미터: {tool_call['args']}")
            
            # 실제 함수 실행 (예시용)
            if tool_call['name'] == 'multiply':
                res = multiply.invoke(tool_call['args'])
            elif tool_call['name'] == 'add':
                res = add.invoke(tool_call['args'])
            elif tool_call['name'] == 'exponentiate':
                res = exponentiate.invoke(tool_call['args'])
            print(f" >> 실행 결과: {res}")
    else:
        print(" AI 답변:", response.content)

# 6. 실습 실행
if __name__ == "__main__":
    run_math_example("3.5와 7을 곱해줘")
    run_math_example("2의 10승이 뭐야?")
    run_math_example("123 더하기 456은?")