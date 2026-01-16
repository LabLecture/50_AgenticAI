from langchain_experimental.tools import PythonREPLTool
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

# 1. 파이썬 코드를 실행하는 도구 생성
python_tool = PythonREPLTool()

# 2. 파이썬 코드를 실행하고 과정을 출력하는 함수
def print_and_execute(code, debug=True):
    # 모델이 반환한 텍스트에서 혹시 모를 마크다운(```python ...) 제거
    clean_code = code.replace("```python", "").replace("```", "").strip()
    
    if debug:
        print("\n--- 생성된 파이썬 코드 ---")
        print(clean_code)
        print("--------------------------")
    
    return python_tool.invoke(clean_code)

# 3. 프롬프트 설정
# 시스템 메시지는 Raymond Hettinger 스타일로 유지합니다.
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are Raymond Hettinger, an expert python programmer. "
            "Return only the raw python code. No explanation, no markdown blocks, no intro. "
            "Just the code itself."
        ),
        ("human", "{input}"),
    ]
)

# 4. LLM 모델 생성 (Ollama로 변경)
# 로컬에 설치된 mistral, llama3, gemma2 등의 모델명을 입력하세요.
llm = ChatOllama(model="mistral:latest", temperature=0)

# 5. 체인 생성 (LCEL)
chain = prompt | llm | StrOutputParser() | RunnableLambda(print_and_execute)

# 6. 결과 실행 및 출력
if __name__ == "__main__":
    result = chain.invoke({"input": "로또 번호 생성기를 출력하는 코드를 작성하세요. 1부터 45까지 숫자 중 6개를 중복없이 정렬하여 출력하세요."})
    print("\n[코드 실행 결과]:")
    print(result)