"""
동시성 제한 테스트 스크립트
10개 이상의 동시 요청을 보내서 동시성 제한이 작동하는지 확인
"""
import asyncio
import aiohttp
import time
from typing import List, Dict


async def send_query(session: aiohttp.ClientSession, query_num: int, base_url: str) -> Dict:
    """단일 쿼리 전송"""
    start_time = time.time()
    
    query_data = {
        "query": f"테스트 쿼리 #{query_num}: 오늘 거래량이 가장 많은 종목은?",
        "session_id": f"test_session_{query_num}",
        "user_id": f"test_user_{query_num}"
    }
    
    try:
        async with session.post(f"{base_url}/query", json=query_data) as response:
            result = await response.json()
            elapsed_time = time.time() - start_time
            
            return {
                "query_num": query_num,
                "success": result.get("success", False),
                "elapsed_time": elapsed_time,
                "error": result.get("error_message"),
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


async def test_concurrency(base_url: str = "http://localhost:8010", num_requests: int = 15):
    """동시성 테스트 실행"""
    print(f"동시성 테스트 시작: {num_requests}개의 동시 요청 전송")
    print(f"서버 URL: {base_url}")
    print("-" * 50)
    
    # 세션 생성
    async with aiohttp.ClientSession() as session:
        # 먼저 동시성 상태 확인
        async with session.get(f"{base_url}/concurrency/status") as response:
            if response.status == 200:
                status = await response.json()
                print("현재 동시성 상태:")
                print(f"  - 최대 동시 접속: {status.get('max_concurrent', 'N/A')}")
                print(f"  - 활성 요청: {status.get('active_requests', 'N/A')}")
                print(f"  - 대기 중인 요청: {status.get('queued_requests', 'N/A')}")
                print("-" * 50)
        
        # 동시에 여러 요청 전송
        start_time = time.time()
        tasks = [send_query(session, i+1, base_url) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # 결과 분석
        print("\n테스트 결과:")
        print("-" * 50)
        
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        print(f"총 요청 수: {num_requests}")
        print(f"성공한 요청: {len(successful_requests)}")
        print(f"실패한 요청: {len(failed_requests)}")
        print(f"전체 소요 시간: {total_time:.2f}초")
        print(f"평균 응답 시간: {sum(r['elapsed_time'] for r in results) / len(results):.2f}초")
        
        # 응답 시간 분포
        print("\n응답 시간 분포:")
        for i in range(0, max(int(r['elapsed_time']) for r in results) + 1):
            count = sum(1 for r in results if i <= r['elapsed_time'] < i+1)
            if count > 0:
                print(f"  {i}-{i+1}초: {'█' * count} ({count}개)")
        
        # 오류가 있는 경우 표시
        if failed_requests:
            print("\n실패한 요청:")
            for req in failed_requests[:5]:  # 최대 5개만 표시
                print(f"  - 요청 #{req['query_num']}: {req['error']}")
        
        # 다시 동시성 상태 확인
        print("\n테스트 후 동시성 상태:")
        async with session.get(f"{base_url}/concurrency/status") as response:
            if response.status == 200:
                status = await response.json()
                print(f"  - 총 요청 수: {status.get('total_requests', 'N/A')}")
                print(f"  - 완료된 요청: {status.get('completed_requests', 'N/A')}")
                print(f"  - 평균 활성 요청: {status.get('average_active', 'N/A'):.2f}")


if __name__ == "__main__":
    # 이벤트 루프 실행
    asyncio.run(test_concurrency())
    
    print("\n추가 테스트를 위한 옵션:")
    print("  - 더 많은 요청 테스트: python test_concurrency.py")
    print("  - 서버 상태 확인: curl http://localhost:8010/concurrency/status")