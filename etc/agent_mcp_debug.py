# agent_mcp_debug.py 개선본
import asyncio
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def debug_mcp_tool():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(current_dir, "youtube_mcp_server.py")

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_script],
        env=os.environ.copy()
    )

    print("=== MCP 도구 단독 테스트 시작 ===\n")
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # 사용 가능한 도구 목록 확인
                tools = await session.list_tools()
                print(f"📋 등록된 도구: {[tool.name for tool in tools.tools]}\n")
                
                # 도구 호출
                print("🔄 서버에 도구 호출 요청 중...")
                test_urls = [
                    "https://www.youtube.com/watch?v=fToUPQ_WRaY",
                    # 추가 테스트 URL
                ]
                
                for url in test_urls:
                    print(f"\n테스트 URL: {url}")
                    result = await session.call_tool(
                        "get_youtube_transcript", 
                        arguments={"video_url": url}
                    )
                    
                    print(f"✅ 결과:\n{result.content[0].text[:200]}...\n")

    except Exception as e:
        print(f"\n❌ 에러 발생:")
        print(f"  타입: {type(e).__name__}")
        print(f"  메시지: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(debug_mcp_tool())