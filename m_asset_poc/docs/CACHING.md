# LLM 캐싱 시스템 가이드

## 개요

M-Asset POC는 Redis 기반의 LLM 응답 캐싱 시스템을 구현하여 동일한 질의에 대한 중복 LLM 호출을 방지하고 응답 속도를 향상시킵니다. 특히 SQL 생성 단계만 캐싱하여 데이터 변경에 유연하게 대응합니다.

## 아키텍처

### 캐싱 전략

1. **SQL 생성만 캐싱**: 답변 생성은 최신 데이터 반영을 위해 캐싱하지 않음
2. **키 생성**: 사용자 쿼리 + 스키마 정보를 SHA-256 해시로 변환
3. **TTL 관리**: 설정 가능한 만료 시간 (기본 1시간)
4. **Redis 백엔드**: 빠른 읽기/쓰기 및 자동 만료 지원

### 캐시 키 구조

```
llm:sql_gen:{sha256_hash}
```

- `llm:sql_gen`: 네임스페이스
- `{sha256_hash}`: 쿼리와 스키마의 조합 해시

## 설정

### 환경 변수

```bash
# LLM 캐싱 설정
LLM_CACHE_ENABLED=true      # 캐싱 활성화 여부
LLM_CACHE_TTL=3600          # TTL (초, 기본 1시간)
LLM_CACHE_MAX_SIZE=10000    # 최대 캐시 항목 수

# Redis 설정
REDIS_HOST=localhost        # Redis 서버 호스트
REDIS_PORT=6379             # Redis 서버 포트
REDIS_DB=0                  # Redis DB 번호
REDIS_PASSWORD=             # Redis 비밀번호 (선택사항)
```

### Redis 설치 및 실행

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:latest
```

## 구현 상세

### LLMCacheManager 클래스

`src/core/llm_cache_manager.py`의 주요 기능:

```python
class LLMCacheManager:
    def __init__(self):
        self.enabled = os.getenv("LLM_CACHE_ENABLED", "true").lower() == "true"
        self.ttl = int(os.getenv("LLM_CACHE_TTL", "3600"))
        self.redis_client = self._create_redis_client()
    
    def get_cached_sql(self, prompt: str, schema_info: str) -> Optional[str]:
        """캐시된 SQL 조회"""
        
    def cache_sql(self, prompt: str, schema_info: str, sql: str) -> bool:
        """SQL 캐싱"""
        
    def _generate_cache_key(self, prompt: str, schema_info: str) -> str:
        """캐시 키 생성 (SHA-256)"""
```

### 통합 예제

```python
# text_to_sql_agent.py에서의 사용
from ..core.llm_cache_manager import llm_cache_manager

# 캐시 확인
cached_sql = llm_cache_manager.get_cached_sql(user_query, schema_info)
if cached_sql:
    logger.info(f"Using cached SQL query: {cached_sql}")
    return {"final_query": cached_sql, "cache_hit": True}

# LLM 호출 후 캐싱
generated_sql = await generate_sql_with_llm(user_query, schema_info)
llm_cache_manager.cache_sql(user_query, schema_info, generated_sql)
```

## 모니터링 및 관리

### 캐시 통계 조회

```bash
curl http://localhost:8010/cache/stats
```

응답 예시:
```json
{
  "success": true,
  "stats": {
    "enabled": true,
    "total_keys": 145,
    "hits": 89,
    "misses": 56,
    "hit_rate": 0.614,
    "memory_usage": "2.3MB",
    "avg_ttl": 2145
  }
}
```

### 캐시 초기화

```bash
curl -X POST http://localhost:8010/cache/clear
```

응답 예시:
```json
{
  "success": true,
  "deleted_count": 145,
  "message": "Successfully cleared 145 cached SQL queries"
}
```

## 성능 최적화

### 1. TTL 조정

- **정적 데이터**: 24시간 이상 (86400초)
- **동적 데이터**: 1-6시간 (3600-21600초)
- **실시간 데이터**: 캐싱 비활성화 권장

### 2. 메모리 관리

```bash
# Redis 메모리 설정
maxmemory 2gb
maxmemory-policy allkeys-lru
```

### 3. 캐시 워밍

```python
# 자주 사용되는 쿼리 미리 캐싱
common_queries = [
    "삼성전자 주가",
    "코스피 상위 10개",
    "오늘의 거래량 순위"
]

for query in common_queries:
    result = text_to_sql_agent.query(query)
```

## 문제 해결

### 1. Redis 연결 실패

**증상**: `redis.exceptions.ConnectionError`

**해결 방법**:
```bash
# Redis 상태 확인
redis-cli ping

# 연결 테스트
redis-cli -h localhost -p 6379
```

### 2. 캐시 미스 높음

**원인**: 쿼리 변형이 많음

**해결 방법**:
- 쿼리 정규화 구현
- 동의어 처리
- 스키마 정보 최소화

### 3. 메모리 부족

**증상**: Redis OOM (Out of Memory)

**해결 방법**:
```bash
# 메모리 사용량 확인
redis-cli info memory

# 캐시 정리
redis-cli FLUSHDB
```

## 모범 사례

### 1. 선택적 캐싱

```python
# 실시간 데이터는 캐싱 제외
if "실시간" in user_query or "현재" in user_query:
    use_cache = False
```

### 2. 캐시 무효화

```python
# 스키마 변경 시 관련 캐시 삭제
def invalidate_schema_cache(table_name: str):
    pattern = f"llm:sql_gen:*{table_name}*"
    for key in redis_client.scan_iter(match=pattern):
        redis_client.delete(key)
```

### 3. 캐시 히트율 모니터링

```python
# 로그에 캐시 히트율 기록
if cache_hit:
    logger.info(f"Cache HIT for query: {query[:50]}...")
else:
    logger.info(f"Cache MISS for query: {query[:50]}...")
```

## 고급 기능

### 1. 캐시 워밍 스크립트

```python
async def warm_cache():
    """자주 사용되는 쿼리 미리 캐싱"""
    queries = load_frequent_queries()
    
    for query in queries:
        try:
            result = await text_to_sql_agent.query(query)
            logger.info(f"Warmed cache for: {query}")
        except Exception as e:
            logger.error(f"Failed to warm cache: {e}")
```

### 2. 캐시 분석

```python
def analyze_cache_patterns():
    """캐시 사용 패턴 분석"""
    keys = redis_client.keys("llm:sql_gen:*")
    
    stats = {
        "total_keys": len(keys),
        "avg_size": 0,
        "ttl_distribution": {},
        "access_patterns": {}
    }
    
    # 분석 로직...
    return stats
```

### 3. 조건부 캐싱

```python
# 복잡도에 따른 캐싱
def should_cache(query: str, execution_time: float) -> bool:
    # 실행 시간이 1초 이상인 쿼리만 캐싱
    if execution_time < 1.0:
        return False
    
    # 집계 함수 포함 쿼리 우선 캐싱
    if any(func in query.upper() for func in ["SUM", "AVG", "COUNT"]):
        return True
    
    return True
```

## 보안 고려사항

### 1. Redis 보안

```bash
# Redis 비밀번호 설정
requirepass your_secure_password

# 바인드 주소 제한
bind 127.0.0.1 ::1
```

### 2. 민감 정보 제외

```python
# 개인정보가 포함된 쿼리는 캐싱 제외
if contains_personal_info(query):
    skip_cache = True
```

### 3. 캐시 키 난독화

- SHA-256 해시 사용으로 원본 쿼리 보호
- 키에 민감 정보 직접 노출 방지

## 향후 개선 사항

1. **분산 캐싱**: Redis Cluster 지원
2. **캐시 계층화**: L1 (메모리) + L2 (Redis)
3. **지능형 TTL**: 사용 빈도에 따른 동적 TTL
4. **캐시 압축**: 대용량 SQL 결과 압축 저장