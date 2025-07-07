#!/usr/bin/env python3
"""
LLM 캐싱 기능 테스트 스크립트
"""
import asyncio
import aiohttp
import json
import time
from datetime import datetime

async def test_cache_stats(session):
    """캐시 통계 조회"""
    url = "http://localhost:8010/cache/stats"
    async with session.get(url) as response:
        result = await response.json()
        print("\n=== 캐시 통계 ===")
        if result.get("success"):
            stats = result["stats"]
            print(f"캐시 활성화: {stats.get('enabled', False)}")
            print(f"캐시된 쿼리 수: {stats.get('cached_queries', 0)}")
            print(f"TTL (초): {stats.get('ttl_seconds', 0)}")
            print(f"히트율: {stats.get('hit_rate', 0):.2f}%")
        else:
            print("캐시 통계 조회 실패")
        return result

async def clear_cache(session):
    """캐시 초기화"""
    url = "http://localhost:8010/cache/clear"
    async with session.post(url) as response:
        result = await response.json()
        print("\n=== 캐시 초기화 ===")
        if result.get("success"):
            print(f"삭제된 항목 수: {result['deleted_count']}")
        else:
            print("캐시 초기화 실패")
        return result

async def send_query(session, query, session_id="test-session"):
    """단일 쿼리 전송"""
    url = "http://localhost:8010/query"
    payload = {
        "query": query,
        "session_id": session_id,
        "user_id": "test-user"
    }
    
    start_time = time.time()
    async with session.post(url, json=payload) as response:
        result = await response.json()
        end_time = time.time()
        
        return {
            "query": query,
            "time": end_time - start_time,
            "success": result.get("success", False),
            "sql": result.get("generated_sql", ""),
            "cached": "(from cache)" in str(result.get("messages", []))
        }

async def test_caching():
    """캐싱 기능 테스트"""
    print("\n=== LLM 캐싱 기능 테스트 시작 ===")
    print(f"시간: {datetime.now()}")
    
    async with aiohttp.ClientSession() as session:
        # 1. 캐시 초기화
        await clear_cache(session)
        
        # 2. 캐시 통계 확인
        await test_cache_stats(session)
        
        # 3. 같은 쿼리를 2번 실행 (첫번째는 캐시 미스, 두번째는 캐시 히트)
        test_queries = [
            "코스피 상위 10개 종목 알려줘",
            "코스닥 시가총액 상위 5개 종목",
            "삼성전자 주가 알려줘"
        ]
        
        print("\n=== 첫번째 실행 (캐시 미스 예상) ===")
        first_results = []
        for query in test_queries:
            result = await send_query(session, query)
            first_results.append(result)
            print(f"쿼리: {query[:30]}... - {result['time']:.2f}초 - 캐시: {result['cached']}")
        
        # 4. 캐시 통계 다시 확인
        print("\n=== 캐시 통계 (첫번째 실행 후) ===")
        stats = await test_cache_stats(session)
        
        # 5. 같은 쿼리 다시 실행 (캐시 히트 예상)
        print("\n=== 두번째 실행 (캐시 히트 예상) ===")
        second_results = []
        for query in test_queries:
            result = await send_query(session, query)
            second_results.append(result)
            print(f"쿼리: {query[:30]}... - {result['time']:.2f}초 - 캐시: {result['cached']}")
        
        # 6. 성능 비교
        print("\n=== 성능 비교 ===")
        for i, query in enumerate(test_queries):
            first_time = first_results[i]['time']
            second_time = second_results[i]['time']
            speedup = first_time / second_time if second_time > 0 else 0
            print(f"{query[:30]}...")
            print(f"  첫번째: {first_time:.2f}초, 두번째: {second_time:.2f}초")
            print(f"  속도 향상: {speedup:.1f}배")
        
        # 7. 최종 캐시 통계
        print("\n=== 최종 캐시 통계 ===")
        await test_cache_stats(session)

if __name__ == "__main__":
    # Redis가 실행 중인지 확인
    print("Redis가 localhost:6379에서 실행 중이어야 합니다.")
    print("LLM_CACHE_ENABLED=true가 설정되어 있어야 합니다.")
    
    asyncio.run(test_caching())