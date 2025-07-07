# 동시성 제어 가이드

## 개요

M-Asset POC는 동시 다발적인 요청을 효율적으로 처리하기 위해 세마포어 기반의 동시성 제한 메커니즘을 구현했습니다. 최대 10명의 동시 사용자를 지원하며, 초과 요청은 대기열에서 관리됩니다.

## 아키텍처

### ConcurrencyLimiter 클래스

`src/core/concurrency_limiter.py`에 구현된 핵심 클래스로, 다음 기능을 제공합니다:

- **세마포어 기반 제한**: asyncio.Semaphore를 사용한 동시 요청 수 제한
- **대기열 관리**: 초과 요청에 대한 자동 대기열 처리
- **타임아웃 처리**: 설정된 시간 초과 시 요청 거부
- **통계 추적**: 실시간 동시성 상태 모니터링

### 동작 원리

```python
# 요청 처리 흐름
1. 클라이언트 요청 수신
2. ConcurrencyLimiter.acquire() 호출
3. 세마포어 획득 시도
   - 성공: 즉시 처리
   - 실패: 대기열 진입
4. 처리 완료 후 세마포어 해제
5. 대기 중인 다음 요청 처리
```

## 설정

### 환경 변수

```bash
# API 서버 동시성 설정
MAX_CONCURRENT_REQUESTS=10        # 최대 동시 요청 수
REQUEST_QUEUE_TIMEOUT=300         # 대기열 타임아웃 (초)

# A2A 서버 동시성 설정
A2A_MAX_CONCURRENT_REQUESTS=10    # A2A 최대 동시 요청 수
A2A_REQUEST_QUEUE_TIMEOUT=300     # A2A 대기열 타임아웃 (초)
```

### 서버별 독립 설정

API 서버와 A2A 서버는 각각 독립적인 동시성 제한기를 사용합니다:

- **API 서버** (port 8010): `concurrency_limiter`
- **A2A 서버** (port 8011): `a2a_concurrency_limiter`

## 사용 예제

### 1. 기본 사용법

```python
from src.core.concurrency_limiter import concurrency_limiter

async def handle_request():
    async with concurrency_limiter.acquire() as request_info:
        wait_time = request_info.get("wait_time", 0.0)
        if wait_time > 0:
            logger.info(f"Request waited {wait_time:.2f}s in queue")
        
        # 실제 작업 수행
        result = await process_query()
        return result
```

### 2. 커스텀 요청 ID 사용

```python
async with concurrency_limiter.acquire(request_id="user_123_req_456"):
    # 요청별 고유 ID로 추적 가능
    pass
```

### 3. 타임아웃 처리

```python
try:
    async with concurrency_limiter.acquire():
        result = await process_query()
except asyncio.TimeoutError:
    return {"error": "요청 대기 시간이 초과되었습니다"}
```

## 모니터링

### 상태 조회 엔드포인트

```bash
# API 서버 동시성 상태
curl http://localhost:8010/concurrency/status

# A2A 서버 동시성 상태
curl http://localhost:8011/concurrency/status
```

### 응답 예시

```json
{
  "max_concurrent": 10,
  "current_active": 3,
  "waiting_requests": 2,
  "total_processed": 156,
  "total_rejected": 0,
  "total_wait_time": 45.3,
  "average_wait_time": 0.29
}
```

## 성능 고려사항

### 1. 동시 요청 수 조정

- **CPU 집약적 작업**: 낮은 값 권장 (5-10)
- **I/O 집약적 작업**: 높은 값 가능 (10-20)
- **메모리 사용량**: 동시 요청당 약 100-200MB 예상

### 2. 타임아웃 설정

- **기본값**: 300초 (5분)
- **복잡한 쿼리**: 600초 이상 권장
- **단순 조회**: 60-120초로 단축 가능

### 3. 대기열 관리

- FIFO (First In, First Out) 방식
- 우선순위 큐는 현재 미지원
- 대기 시간은 응답에 포함됨

## 문제 해결

### 1. "요청 대기 시간 초과" 오류

**원인**: 대기열에서 타임아웃 시간을 초과

**해결 방법**:
- `REQUEST_QUEUE_TIMEOUT` 값 증가
- 동시 요청 수 제한 완화
- 서버 리소스 확인 및 증설

### 2. 높은 대기 시간

**원인**: 동시 요청이 한계에 도달

**해결 방법**:
- `MAX_CONCURRENT_REQUESTS` 값 증가
- 쿼리 최적화로 처리 시간 단축
- 캐싱 활용도 증가

### 3. 메모리 부족

**원인**: 너무 많은 동시 요청 처리

**해결 방법**:
- 동시 요청 수 감소
- 서버 메모리 증설
- 쿼리 결과 크기 제한

## 모범 사례

### 1. 적절한 동시성 수준 설정

```python
# 서버 리소스에 맞춰 조정
# CPU 코어 수 * 2-4 권장
MAX_CONCURRENT_REQUESTS = cpu_count() * 2
```

### 2. 요청 ID 활용

```python
# 사용자별 추적
request_id = f"user_{user_id}_session_{session_id}"

# 로그 분석 용이
async with concurrency_limiter.acquire(request_id=request_id):
    logger.info(f"Processing request: {request_id}")
```

### 3. 예외 처리

```python
try:
    async with concurrency_limiter.acquire() as info:
        if info["wait_time"] > 10:
            logger.warning(f"Long wait time: {info['wait_time']}s")
        return await process_query()
except asyncio.TimeoutError:
    return {"error": "시스템이 바쁩니다. 잠시 후 다시 시도해주세요."}
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

## Python 버전 호환성

### Python 3.10 이하

```python
# asyncio.timeout 대신 asyncio.wait_for 사용
await asyncio.wait_for(
    self._semaphore.acquire(),
    timeout=self.timeout
)
```

### Python 3.11 이상

```python
# asyncio.timeout 사용 가능
async with asyncio.timeout(self.timeout):
    await self._semaphore.acquire()
```

## 향후 개선 사항

1. **우선순위 큐**: VIP 사용자나 중요 요청 우선 처리
2. **동적 스케일링**: 부하에 따른 자동 동시성 조정
3. **분산 동시성**: 여러 서버 간 동시성 조율
4. **상세 메트릭**: Prometheus/Grafana 연동