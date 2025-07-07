"""
LLM 응답 캐싱 매니저
SQL 생성 LLM 응답만 캐싱 (답변 생성은 제외)
"""

import os
import redis
import json
import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import timedelta
import pickle

from .config import config

logger = logging.getLogger(__name__)


class LLMCacheManager:
    """LLM 응답 캐싱 관리 클래스"""
    
    def __init__(self):
        """LLM 캐시 매니저 초기화"""
        self._redis_client = None
        self._enabled = False
        self._ttl = 3600  # 기본 TTL: 1시간
        
    def initialize(self):
        """Redis 클라이언트 초기화"""
        try:
            # 환경 변수에서 설정 읽기
            self._enabled = os.getenv("LLM_CACHE_ENABLED", "false").lower() == "true"
            
            if not self._enabled:
                logger.info("LLM caching is disabled")
                return
            
            # Redis 연결 설정
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_db = int(os.getenv("REDIS_DB", "0"))
            redis_password = os.getenv("REDIS_PASSWORD")
            
            # 빈 문자열은 None으로 처리
            if not redis_password or redis_password == "":
                redis_password = None
            
            # TTL 설정 (초 단위)
            self._ttl = int(os.getenv("LLM_CACHE_TTL", "3600"))
            
            # Redis 연결 정보 로깅
            logger.info(f"Connecting to Redis at {redis_host}:{redis_port}, DB: {redis_db}")
            logger.info(f"Password configured: {'Yes' if redis_password else 'No'}")
            
            # Redis 클라이언트 생성
            self._redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=False,  # 바이너리 데이터 저장을 위해
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # 연결 테스트
            self._redis_client.ping()
            logger.info(f"LLM cache initialized - Redis connected at {redis_host}:{redis_port}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM cache: {e}")
            self._enabled = False
            self._redis_client = None
    
    def _generate_cache_key(self, prompt: str, schema_info: str) -> str:
        """캐시 키 생성 (프롬프트 + 스키마 정보 해시)"""
        # 프롬프트와 스키마 정보를 결합하여 고유 키 생성
        combined = f"{prompt}::::{schema_info}"
        hash_object = hashlib.sha256(combined.encode())
        return f"llm:sql_gen:{hash_object.hexdigest()}"
    
    def get_cached_sql(self, prompt: str, schema_info: str) -> Optional[str]:
        """캐시된 SQL 쿼리 조회"""
        if not self._enabled or not self._redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(prompt, schema_info)
            cached_data = self._redis_client.get(cache_key)
            
            if cached_data:
                # 캐시 히트 로깅
                logger.info(f"Cache HIT for SQL generation")
                result = pickle.loads(cached_data)
                return result.get("sql_query")
            
            logger.debug(f"Cache MISS for SQL generation")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            return None
    
    def set_cached_sql(self, prompt: str, schema_info: str, sql_query: str) -> bool:
        """SQL 쿼리 캐싱"""
        if not self._enabled or not self._redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(prompt, schema_info)
            cache_data = {
                "sql_query": sql_query,
                "prompt": prompt[:100],  # 디버깅용 프롬프트 일부 저장
                "cached_at": json.dumps({"timestamp": str(config.get_current_time())})
            }
            
            # 데이터 직렬화 및 저장
            serialized_data = pickle.dumps(cache_data)
            self._redis_client.setex(
                cache_key,
                timedelta(seconds=self._ttl),
                serialized_data
            )
            
            logger.info(f"SQL query cached with TTL={self._ttl}s")
            return True
            
        except Exception as e:
            logger.error(f"Error caching SQL query: {e}")
            return False
    
    def clear_all_cache(self) -> int:
        """모든 LLM 캐시 초기화"""
        if not self._enabled or not self._redis_client:
            return 0
        
        try:
            # llm:sql_gen:* 패턴의 모든 키 삭제
            pattern = "llm:sql_gen:*"
            keys = self._redis_client.keys(pattern)
            
            if keys:
                deleted_count = self._redis_client.delete(*keys)
                logger.info(f"Cleared {deleted_count} cached SQL queries")
                return deleted_count
            
            logger.info("No cached SQL queries to clear")
            return 0
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보 반환"""
        if not self._enabled or not self._redis_client:
            return {"enabled": False, "error": "Cache not enabled or not connected"}
        
        try:
            # 캐시된 항목 수 계산
            pattern = "llm:sql_gen:*"
            keys = self._redis_client.keys(pattern)
            
            # Redis 정보 가져오기
            info = self._redis_client.info()
            
            return {
                "enabled": True,
                "connected": True,
                "cached_queries": len(keys),
                "ttl_seconds": self._ttl,
                "redis_version": info.get("redis_version", "unknown"),
                "used_memory": info.get("used_memory_human", "unknown"),
                "total_connections": info.get("total_connections_received", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"enabled": True, "connected": False, "error": str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """캐시 히트율 계산"""
        total = hits + misses
        if total == 0:
            return 0.0
        return (hits / total) * 100
    
    def is_enabled(self) -> bool:
        """캐싱 활성화 여부 반환"""
        return self._enabled and self._redis_client is not None
    
    def close(self):
        """Redis 연결 종료"""
        if self._redis_client:
            try:
                self._redis_client.close()
                logger.info("LLM cache connection closed")
            except Exception as e:
                logger.error(f"Error closing cache connection: {e}")


# 전역 LLM 캐시 매니저 인스턴스
llm_cache_manager = LLMCacheManager()