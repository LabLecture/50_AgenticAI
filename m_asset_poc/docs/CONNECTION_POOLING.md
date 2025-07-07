# Weaviate 연결 풀링 가이드

## 개요

M-Asset POC는 Weaviate 벡터 스토어에 대한 효율적인 연결 관리를 위해 커스텀 연결 풀을 구현했습니다. 이를 통해 연결 오버헤드를 줄이고 동시 요청 처리 성능을 향상시킵니다.

## 아키텍처

### WeaviateConnectionPool 클래스

`src/core/weaviate_pool.py`에 구현된 연결 풀은 다음 기능을 제공합니다:

- **연결 생명주기 관리**: 생성, 재사용, 종료
- **헬스 체크**: 주기적인 연결 상태 확인
- **자동 재연결**: 실패한 연결 자동 복구
- **통계 추적**: 연결 사용 패턴 모니터링

### 연결 풀 동작 원리

```
1. 초기화 시 최소 연결 수만큼 생성
2. 요청 시 가용 연결 할당
3. 사용 후 연결 반환 (재사용)
4. 주기적 헬스 체크로 불량 연결 제거
5. 필요시 최대 한계까지 동적 확장
```

## 설정

### 환경 변수

```bash
# 연결 풀 기본 설정
VECTOR_STORE_USE_POOL=true              # 연결 풀 사용 여부
VECTOR_STORE_MIN_CONNECTIONS=2          # 최소 연결 수
VECTOR_STORE_MAX_CONNECTIONS=10         # 최대 연결 수
VECTOR_STORE_CONNECTION_LIFETIME=3600   # 연결 수명 (초)
VECTOR_STORE_HEALTH_CHECK_INTERVAL=60   # 헬스 체크 간격 (초)

# Weaviate 서버 설정
WEAVIATE_HOST=localhost                 # Weaviate 호스트
WEAVIATE_PORT=8080                      # Weaviate 포트
```

### 연결 풀 vs 단일 연결

```python
# 연결 풀 사용 (권장)
VECTOR_STORE_USE_POOL=true

# 단일 연결 사용 (레거시)
VECTOR_STORE_USE_POOL=false
```

## 구현 상세

### 연결 관리

```python
class WeaviateConnection:
    """개별 Weaviate 연결 래퍼"""
    def __init__(self, host: str, port: int, connection_id: int):
        self.client = None
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        self.in_use = False
```

### 컨텍스트 매니저 사용

```python
# 자동 연결 관리
with weaviate_pool.get_connection() as client:
    # Weaviate 작업 수행
    results = client.collections.get("collection_name").query(...)
# 연결 자동 반환
```

## 사용 예제

### 1. 벡터 검색

```python
from src.core.weaviate_pool import weaviate_pool

# 연결 풀에서 연결 가져오기
with weaviate_pool.get_connection() as client:
    collection = client.collections.get("m_asset_schema")
    results = collection.query.hybrid(
        query="삼성전자",
        limit=5
    )
```

### 2. 타임아웃 처리

```python
try:
    with weaviate_pool.get_connection(timeout=10.0) as client:
        # 10초 내에 연결 획득
        results = perform_search(client)
except TimeoutError:
    logger.error("연결 풀에서 연결을 가져올 수 없습니다")
```

### 3. 통계 조회

```python
stats = weaviate_pool.get_stats()
print(f"활성 연결: {stats['current_active']}")
print(f"대기 연결: {stats['current_idle']}")
print(f"평균 대기 시간: {stats['avg_wait_time']:.2f}초")
```

## 모니터링

### 연결 풀 상태 엔드포인트

```bash
curl http://localhost:8010/vector-store/pool/stats
```

응답 예시:
```json
{
  "success": true,
  "stats": {
    "enabled": true,
    "total_connections": 5,
    "current_active": 2,
    "current_idle": 3,
    "available_connections": 3,
    "total_connections_created": 8,
    "total_connections_closed": 3,
    "total_requests": 156,
    "avg_wait_time": 0.05,
    "health_check_failures": 1
  }
}
```

## 성능 최적화

### 1. 연결 수 조정

```bash
# 동시 사용자가 적은 경우
VECTOR_STORE_MIN_CONNECTIONS=1
VECTOR_STORE_MAX_CONNECTIONS=5

# 동시 사용자가 많은 경우
VECTOR_STORE_MIN_CONNECTIONS=5
VECTOR_STORE_MAX_CONNECTIONS=20
```

### 2. 연결 수명 관리

```bash
# 안정적인 환경
VECTOR_STORE_CONNECTION_LIFETIME=3600  # 1시간

# 불안정한 네트워크
VECTOR_STORE_CONNECTION_LIFETIME=600   # 10분
```

### 3. 헬스 체크 빈도

```bash
# 일반적인 경우
VECTOR_STORE_HEALTH_CHECK_INTERVAL=60  # 1분

# 중요한 프로덕션
VECTOR_STORE_HEALTH_CHECK_INTERVAL=30  # 30초
```

## 문제 해결

### 1. 연결 획득 실패

**증상**: `TimeoutError: Failed to get connection within 30 seconds`

**해결 방법**:
- 최대 연결 수 증가
- Weaviate 서버 상태 확인
- 네트워크 연결 확인

### 2. 빈번한 헬스 체크 실패

**증상**: 로그에 "Dead connection detected" 반복

**해결 방법**:
- Weaviate 서버 안정성 확인
- 연결 수명 단축
- 네트워크 품질 개선

### 3. 메모리 사용량 증가

**원인**: 너무 많은 연결 유지

**해결 방법**:
```python
# 최대 연결 수 제한
VECTOR_STORE_MAX_CONNECTIONS=5

# 연결 수명 단축
VECTOR_STORE_CONNECTION_LIFETIME=1800
```

## 모범 사례

### 1. 적절한 풀 크기 설정

```python
# 권장 공식
MIN_CONNECTIONS = 동시_사용자_수 * 0.5
MAX_CONNECTIONS = 동시_사용자_수 * 2
```

### 2. 연결 재사용 최대화

```python
# 나쁜 예: 매번 새 연결
for query in queries:
    client = weaviate.connect_to_local()
    result = search(client, query)
    client.close()

# 좋은 예: 연결 재사용
with weaviate_pool.get_connection() as client:
    for query in queries:
        result = search(client, query)
```

### 3. 예외 처리

```python
def safe_vector_search(query: str) -> List[str]:
    try:
        with weaviate_pool.get_connection() as client:
            return perform_search(client, query)
    except TimeoutError:
        logger.warning("연결 풀 타임아웃, 단일 연결 시도")
        return fallback_search(query)
    except Exception as e:
        logger.error(f"벡터 검색 실패: {e}")
        return []
```

## 고급 기능

### 1. 연결 풀 워밍

```python
def warm_connection_pool():
    """시작 시 연결 풀 미리 준비"""
    for _ in range(weaviate_pool.min_connections):
        try:
            with weaviate_pool.get_connection(timeout=5.0) as client:
                client.is_ready()  # 연결 테스트
        except Exception as e:
            logger.error(f"연결 풀 워밍 실패: {e}")
```

### 2. 동적 크기 조정

```python
def adjust_pool_size(current_load: int):
    """부하에 따른 풀 크기 조정"""
    if current_load > 80:  # 80% 이상 부하
        weaviate_pool.max_connections = min(20, weaviate_pool.max_connections + 2)
    elif current_load < 20:  # 20% 이하 부하
        weaviate_pool.max_connections = max(5, weaviate_pool.max_connections - 2)
```

### 3. 연결별 메트릭

```python
def get_connection_metrics():
    """개별 연결 상태 조회"""
    metrics = []
    for conn in weaviate_pool._connections:
        metrics.append({
            "id": conn.connection_id,
            "age": (datetime.now() - conn.created_at).total_seconds(),
            "last_used": (datetime.now() - conn.last_used).total_seconds(),
            "in_use": conn.in_use,
            "alive": conn.is_alive()
        })
    return metrics
```

## 연결 풀 비활성화

특정 상황에서 연결 풀을 비활성화해야 할 경우:

```bash
# 연결 풀 비활성화
VECTOR_STORE_USE_POOL=false
```

비활성화가 필요한 경우:
- 디버깅 시
- 연결 수가 매우 적은 환경
- Weaviate 서버가 로컬인 경우

## 향후 개선 사항

1. **연결 우선순위**: 중요 요청에 우선 연결 할당
2. **연결 그룹화**: 읽기/쓰기 연결 분리
3. **자동 스케일링**: 부하 기반 동적 조정
4. **분산 풀**: 여러 Weaviate 인스턴스 지원
5. **연결 암호화**: TLS/SSL 지원 강화