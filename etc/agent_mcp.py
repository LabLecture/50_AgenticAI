# agent_mcp.py 소스
import asyncio
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

async def run_youtube_agent():
    # [1]. 외부 도구(MCP 서버) 실행을 위한 환경 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(current_dir, "youtube_mcp_server.py")

    # 서버 실행 파라미터: 현재 가상환경의 python으로 서버 파일을 실행하도록 설정
    server_params = StdioServerParameters(
        command=sys.executable, 
        args=[server_script],
        env=os.environ.copy()
    )

    try:
        # [2]. MCP 서버 프로세스 연결 (표준 입출력 통로 개설)
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:                
                await session.initialize()  # MCP 프로토콜 초기화 (핸드셰이크)
                print("--- MCP 서버 연결 완료 ---")

                llm = ChatOllama(model="qwen3:8b")

                # [3]. 도구 정의 (LLM에게 "너는 이런 도구를 쓸 수 있어"라고 명세 전달)
                # JSON 구조 -> LLM의 도구 이름을 부르고 인자를 채우는 기준
                tools_spec = [{
                    "name": "get_youtube_transcript",
                    "description": "유튜브 비디오 URL에서 자막을 가져옵니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {"video_url": {"type": "string"}},
                        "required": ["video_url"]
                    }
                }]
                
                llm_with_tools = llm.bind_tools(tools_spec) # 모델에 도구 정보를 바인딩

                youtube_url = "https://www.youtube.com/watch?v=fToUPQ_WRaY"
                messages = [
                    SystemMessage(content=(
                        "너는 유튜브 분석 전문가야. "
                        "사용자가 링크를 주면 무조건 'get_youtube_transcript' 도구를 사용해 자막을 먼저 가져와. "
                        "자막 데이터가 없으면 절대로 요약하지 말고 모른다고 답해."
                    )),
                    HumanMessage(content=f"이 영상 한글로 요약해줘: {youtube_url}")
                ]

                # [4]. [에이전트 루프 - 1단계] 추론(Reasoning)
                # LLM이 질문을 받고 "도구를 실행해야겠다"고 결정하는 단계
                print("\n[에이전트 생각 중...]")
                ai_msg = await llm_with_tools.ainvoke(messages)
                messages.append(ai_msg)

                # [5]. [에이전트 루프 - 2단계] 행동(Action)
                # LLM이 내린 도구 실행 명령(tool_calls)이 있는지 확인
                if ai_msg.tool_calls:
                    for tool_call in ai_msg.tool_calls:
                        print(f"--- 도구 실제 실행 중: {tool_call['name']} ---")
                        
                        # MCP 서버 세션을 통해 실제로 자막 데이터를 긁어옴
                        mcp_result = await session.call_tool(
                            tool_call["name"], 
                            arguments=tool_call["args"]
                        )
                        
                        # 도구로부터 받은 자막 원문을 대화 기록에 추가 (Observation)
                        transcript_text = mcp_result.content[0].text
                        messages.append(ToolMessage(
                            content=transcript_text, 
                            tool_call_id=tool_call["id"]
                        ))

                    # [6]. [에이전트 루프 - 3단계] 최종 답변(Final Answer)
                    # 획득한 자막 데이터를 바탕으로 LLM이 다시 요약을 수행
                    print("[최종 답변 생성 중...]")
                    final_answer = await llm_with_tools.ainvoke(messages)
                    
                    print("\n" + "="*50)
                    print("[최종 요약 결과]\n")
                    print(final_answer.content)
                    print("="*50)
                else:
                    # 도구 호출을 안 하고 대답하는 경우(Hallucination)에 대한 예외 처리
                    print("\n⚠️ AI가 도구를 호출하지 않고 답변했습니다:")
                    print(ai_msg.content)

    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    # Windows에서 비동기 입출력을 지원하기 위한 이벤트 루프 정책 설정
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_youtube_agent())