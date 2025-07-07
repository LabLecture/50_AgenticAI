#!/usr/bin/env python3
"""
A2A 서버 캐싱 테스트
"""
import asyncio
import aiohttp
import json
import time
from datetime import datetime

async def send_a2a_request(session, message_id, query):
    """A2A 요청 전송"""
    url = "http://localhost:8011/"
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "messageId": message_id,
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
    async with session.post(url, json=payload) as response:
        result = await response.json()
        end_time = time.time()
        
        # 결과에서 답변 추출
        answer = "Error"
        if "result" in result and "parts" in result["result"]:
            parts = result["result"]["parts"]
            if parts and isinstance(parts[0], dict) and "text" in parts[0]:
                answer = parts[0]["text"]
                # JSON 형식인 경우 파싱
                try:
                    parsed = json.loads(answer)
                    answer = f"SQL: {parsed.get('sql', 'N/A')[:50]}..."
                except:
                    answer = answer[:100] + "..." if len(answer) > 100 else answer
        
        return {
            "message_id": message_id,
            "query": query,
            "time": end_time - start_time,
            "answer": answer
        }

async def test_a2a_caching():
    """A2A 캐싱 테스트"""
    print("\n=== A2A 서버 LLM 캐싱 테스트 ===")
    print(f"시간: {datetime.now()}")
    
    async with aiohttp.ClientSession() as session:
        # 캐시 초기화
        print("\n1. 캐시 초기화")
        async with session.post("http://localhost:8010/cache/clear") as resp:
            result = await resp.json()
            print(f"   삭제된 항목: {result.get('deleted_count', 0)}")
        
        # 첫 번째 요청 (캐시 미스)
        print("\n2. 첫 번째 요청 (캐시 미스 예상)")
        queries = [
            "코스피 상위 5개 종목",
            "삼성전자 최근 주가",
            "외국인 보유 비율 높은 종목"
        ]
        
        first_results = []
        for i, query in enumerate(queries):
            result = await send_a2a_request(session, f"test-cache-{i}", query)
            first_results.append(result)
            print(f"   {query}: {result['time']:.2f}초")
        
        # 캐시 상태 확인
        print("\n3. 캐시 상태 확인")
        async with session.get("http://localhost:8010/cache/stats") as resp:
            stats = await resp.json()
            if stats.get("success") and "stats" in stats:
                cache_stats = stats["stats"]
                print(f"   캐시된 쿼리: {cache_stats.get('cached_queries', 0)}")
                print(f"   히트율: {cache_stats.get('hit_rate', 0):.1f}%")
        
        # 두 번째 요청 (캐시 히트)
        print("\n4. 두 번째 요청 (캐시 히트 예상)")
        second_results = []
        for i, query in enumerate(queries):
            result = await send_a2a_request(session, f"test-cache-second-{i}", query)
            second_results.append(result)
            print(f"   {query}: {result['time']:.2f}초")
        
        # 성능 비교
        print("\n5. 성능 비교")
        for i in range(len(queries)):
            first_time = first_results[i]['time']
            second_time = second_results[i]['time']
            speedup = first_time / second_time if second_time > 0 else 0
            print(f"   {queries[i]}: {first_time:.2f}초 → {second_time:.2f}초 (속도향상: {speedup:.1f}배)")
        
        # 최종 캐시 상태
        print("\n6. 최종 캐시 상태")
        async with session.get("http://localhost:8010/cache/stats") as resp:
            stats = await resp.json()
            if stats.get("success") and "stats" in stats:
                cache_stats = stats["stats"]
                print(f"   캐시된 쿼리: {cache_stats.get('cached_queries', 0)}")
                print(f"   히트율: {cache_stats.get('hit_rate', 0):.1f}%")

if __name__ == "__main__":
    asyncio.run(test_a2a_caching())