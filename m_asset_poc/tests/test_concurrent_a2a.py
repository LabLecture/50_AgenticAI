#!/usr/bin/env python3
"""
A2A 서버 동시성 테스트 스크립트
"""
import asyncio
import aiohttp
import json
import time
from datetime import datetime

async def send_a2a_request(session, request_id, query):
    """단일 A2A 요청 전송"""
    url = "http://localhost:8011/"
    payload = {
        "id": request_id,
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "messageId": f"test-{request_id}",
                "role": "user",
                "parts": [
                    {
                        "text": query
                    }
                ]
            }
        }
    }
    
    start_time = time.time()
    try:
        async with session.post(url, json=payload) as response:
            result = await response.json()
            end_time = time.time()
            
            # 결과에서 답변 추출
            answer = "Error"
            if "result" in result and "parts" in result["result"]:
                parts = result["result"]["parts"]
                if parts and "text" in parts[0]:
                    answer = parts[0]["text"][:100] + "..." if len(parts[0]["text"]) > 100 else parts[0]["text"]
            
            return {
                "id": request_id,
                "query": query,
                "time": end_time - start_time,
                "answer": answer,
                "success": "error" not in result
            }
    except Exception as e:
        end_time = time.time()
        return {
            "id": request_id,
            "query": query,
            "time": end_time - start_time,
            "answer": str(e),
            "success": False
        }

async def test_concurrent_requests(num_requests=15):
    """동시 요청 테스트"""
    queries = [
        "코스피 상위 10개 종목 알려줘",
        "코스닥 시가총액 상위 5개 종목",
        "삼성전자 주가 알려줘",
        "최근 거래량이 많은 종목 5개",
        "외국인 보유 비율이 높은 종목",
    ]
    
    print(f"\n=== A2A 서버 동시성 테스트 시작 ===")
    print(f"시간: {datetime.now()}")
    print(f"동시 요청 수: {num_requests}")
    print(f"최대 동시 처리: 10 (설정값)")
    print("="*50)
    
    async with aiohttp.ClientSession() as session:
        # 요청 생성
        tasks = []
        for i in range(num_requests):
            query = queries[i % len(queries)]
            task = send_a2a_request(session, i+1, query)
            tasks.append(task)
        
        # 동시 실행
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
    # 결과 분석
    print("\n=== 실행 결과 ===")
    successful = sum(1 for r in results if r["success"])
    failed = num_requests - successful
    
    print(f"총 실행 시간: {total_time:.2f}초")
    print(f"성공: {successful}, 실패: {failed}")
    print(f"평균 응답 시간: {sum(r['time'] for r in results) / len(results):.2f}초")
    
    # 상세 결과
    print("\n=== 상세 결과 ===")
    for result in results[:5]:  # 처음 5개만 표시
        print(f"ID {result['id']}: {result['query'][:30]}... - {result['time']:.2f}초 - {'성공' if result['success'] else '실패'}")
        print(f"   답변: {result['answer'][:80]}...")
    
    if num_requests > 5:
        print(f"... 외 {num_requests - 5}개 요청")
    
    # 대기 시간 분석
    wait_times = []
    for i, result in enumerate(results):
        if i >= 10:  # 11번째 요청부터는 대기가 있었을 것
            expected_min_time = results[i-10]['time']  # 10개 전 요청이 끝난 후 시작
            if result['time'] > expected_min_time:
                wait_times.append(result['time'] - expected_min_time)
    
    if wait_times:
        print(f"\n예상 대기 시간 (11번째 요청부터): 평균 {sum(wait_times)/len(wait_times):.2f}초")

if __name__ == "__main__":
    asyncio.run(test_concurrent_requests(15))