"""
A2A 서버 동시성 테스트 스크립트
여러 A2A 메시지를 동시에 전송하여 비동기 처리 확인
"""
import asyncio
import aiohttp
import json
import time
from typing import List, Dict


async def send_a2a_message(session: aiohttp.ClientSession, query_num: int, base_url: str) -> Dict:
    """A2A 프로토콜로 메시지 전송"""
    start_time = time.time()
    
    # A2A 메시지 형식
    message_data = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "messageId": f"test_msg_{query_num}",
                "role": "user",
                "parts": [
                    {
                        "kind": "text",
                        "text": f"테스트 쿼리 #{query_num}: 삼성전자의 현재 주가는 얼마인가요?"
                    }
                ],
                "createdAt": "2025-06-30T12:00:00Z"
            }
        },
        "id": f"req_{query_num}"
    }
    
    try:
        async with session.post(f"{base_url}/", json=message_data) as response:
            result = await response.json()
            elapsed_time = time.time() - start_time
            
            # A2A 응답에서 텍스트 추출
            response_text = ""
            if "result" in result and "parts" in result.get("result", {}):
                parts = result["result"]["parts"]
                for part in parts:
                    if isinstance(part, dict) and "text" in part:
                        response_text += part["text"]
            
            return {
                "query_num": query_num,
                "success": "error" not in result,
                "elapsed_time": elapsed_time,
                "response": response_text[:100] + "..." if len(response_text) > 100 else response_text,
                "status_code": response.status
            }
    except Exception as e:
        elapsed_time = time.time() - start_time
        return {
            "query_num": query_num,
            "success": False,
            "elapsed_time": elapsed_time,
            "error": str(e),
            "status_code": -1
        }


async def test_a2a_concurrency(base_url: str = "http://localhost:8011", num_requests: int = 15):
    """A2A 서버 동시성 테스트"""
    print(f"A2A 서버 동시성 테스트 시작: {num_requests}개의 동시 요청 전송")
    print(f"서버 URL: {base_url}")
    print("-" * 60)
    
    # 세션 생성
    async with aiohttp.ClientSession() as session:
        # 먼저 동시성 상태 확인
        async with session.get(f"{base_url}/concurrency/status") as response:
            if response.status == 200:
                status = await response.json()
                print("현재 A2A 서버 동시성 상태:")
                print(f"  - 최대 동시 접속: {status.get('max_concurrent', 'N/A')}")
                print(f"  - 활성 요청: {status.get('active_requests', 'N/A')}")
                print(f"  - 대기 중인 요청: {status.get('queued_requests', 'N/A')}")
                print("-" * 60)
        
        # 동시에 여러 A2A 메시지 전송
        print("\n동시 요청 전송 중...")
        start_time = time.time()
        tasks = [send_a2a_message(session, i+1, base_url) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # 결과 분석
        print("\n테스트 결과:")
        print("-" * 60)
        
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        print(f"총 요청 수: {num_requests}")
        print(f"성공한 요청: {len(successful_requests)}")
        print(f"실패한 요청: {len(failed_requests)}")
        print(f"전체 소요 시간: {total_time:.2f}초")
        
        if successful_requests:
            avg_time = sum(r['elapsed_time'] for r in successful_requests) / len(successful_requests)
            print(f"평균 응답 시간: {avg_time:.2f}초")
        
        # 응답 시간 분포
        print("\n응답 시간 분포:")
        time_ranges = {}
        for r in results:
            time_sec = int(r['elapsed_time'])
            time_ranges[time_sec] = time_ranges.get(time_sec, 0) + 1
        
        for sec in sorted(time_ranges.keys()):
            count = time_ranges[sec]
            print(f"  {sec}-{sec+1}초: {'█' * count} ({count}개)")
        
        # 처음 5개 요청의 결과 표시
        print("\n처음 5개 요청 결과:")
        for r in results[:5]:
            if r["success"]:
                print(f"  - 요청 #{r['query_num']}: {r['elapsed_time']:.2f}초, 응답: {r['response']}")
            else:
                print(f"  - 요청 #{r['query_num']}: 실패 - {r.get('error', 'Unknown error')}")
        
        # 다시 동시성 상태 확인
        print("\n테스트 후 A2A 서버 동시성 상태:")
        async with session.get(f"{base_url}/concurrency/status") as response:
            if response.status == 200:
                status = await response.json()
                print(f"  - 총 요청 수: {status.get('total_requests', 'N/A')}")
                print(f"  - 활성 요청: {status.get('active_requests', 'N/A')}")
                print(f"  - 평균 활성 요청: {status.get('average_active', 'N/A'):.2f}")
                
        # 시스템 전체 상태 확인
        print("\nA2A 서버 시스템 상태:")
        async with session.get(f"{base_url}/status") as response:
            if response.status == 200:
                status = await response.json()
                print(f"  - 서버: {status.get('server', 'N/A')}")
                print(f"  - A2A 활성화: {status.get('a2a_enabled', 'N/A')}")
                print(f"  - 에이전트 이름: {status.get('agent_name', 'N/A')}")


if __name__ == "__main__":
    # 이벤트 루프 실행
    asyncio.run(test_a2a_concurrency())
    
    print("\n추가 테스트:")
    print("  - 더 많은 요청: python test_a2a_concurrency.py")
    print("  - 스트리밍 테스트: A2A message/stream 메서드 사용")