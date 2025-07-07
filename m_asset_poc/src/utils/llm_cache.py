"""
LLM response caching module using Redis.
Caches LLM responses to reduce API calls and improve performance.
"""

import redis
from redis import Redis
from typing import Optional, Any, Dict
import json
import hashlib
import time
import logging
from datetime import datetime
import os

from ..core.config import config

logger = logging.getLogger(__name__)


class LLMCache:
    """LLM 응답 캐싱 클래스"""
    
    def __init__(self):
        """LLM 캐시 초기화"""
        self._redis_client: Optional[Redis] = None
        self._enabled = os.getenv("LLM_CACHE_ENABLED", "true").lower() == "true"
        self._ttl = int(os.getenv("LLM_CACHE_TTL", "3600"))  # 기본 1시간
        self._max_size = int(os.getenv("LLM_CACHE_MAX_SIZE", "10000"))
        self._hit_count = 0
        self._miss_count = 0
        self._error_count = 0
        
        if self._enabled:
            self._initialize_redis()
    
    def _initialize_redis(self):
        """Redis 클라이언트 초기화"""
        try:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_db = int(os.getenv("REDIS_DB", "0"))
            redis_password = os.getenv("REDIS_PASSWORD")
            
            self._redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # 연결 테스트
            self._redis_client.ping()
            logger.info(f"Redis cache initialized successfully at {redis_host}:{redis_port}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            logger.warning("LLM caching will be disabled")
            self._enabled = False
            self._redis_client = None
    
    def _generate_cache_key(self, prompt: str, model: str, temperature: float = 0.0) -> str:
        """
        프롬프트와 모델 정보로 캐시 키 생성
        
        Args:
            prompt: LLM 프롬프트
            model: 모델 이름
            temperature: 온도 설정
            
        Returns:
            str: 캐시 키
        """
        # 캐시 키 생성을 위한 정보 조합
        cache_data = {
            "prompt": prompt,
            "model": model,
            "temperature": temperature
        }
        
        # SHA256 해시로 캐시 키 생성
        cache_string = json.dumps(cache_data, sort_keys=True)
        cache_key = f"llm_cache:{hashlib.sha256(cache_string.encode()).hexdigest()}"
        
        return cache_key
    
    def get(self, prompt: str, model: str, temperature: float = 0.0) -> Optional[str]:
        """
        캐시에서 LLM 응답 조회
        
        Args:
            prompt: LLM 프롬프트
            model: 모델 이름
            temperature: 온도 설정
            
        Returns:
            Optional[str]: 캐시된 응답 (없으면 None)
        """
        if not self._enabled or not self._redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(prompt, model, temperature)
            cached_response = self._redis_client.get(cache_key)
            
            if cached_response:
                self._hit_count += 1
                
                # 캐시 메타데이터 업데이트
                meta_key = f"{cache_key}:meta"
                self._redis_client.hincrby(meta_key, "hit_count", 1)
                self._redis_client.hset(meta_key, "last_accessed", datetime.now().isoformat())
                
                logger.debug(f"Cache hit for key: {cache_key[:16]}...")
                return cached_response
            else:
                self._miss_count += 1
                logger.debug(f"Cache miss for key: {cache_key[:16]}...")
                return None
                
        except Exception as e:
            self._error_count += 1
            logger.error(f"Error retrieving from cache: {e}")
            return None
    
    def set(self, prompt: str, model: str, response: str, temperature: float = 0.0, ttl: Optional[int] = None):
        """
        LLM 응답을 캐시에 저장
        
        Args:
            prompt: LLM 프롬프트
            model: 모델 이름
            response: LLM 응답
            temperature: 온도 설정
            ttl: TTL 오버라이드 (초)
        """
        if not self._enabled or not self._redis_client:
            return
        
        try:
            cache_key = self._generate_cache_key(prompt, model, temperature)
            ttl = ttl or self._ttl
            
            # 응답 저장
            self._redis_client.setex(cache_key, ttl, response)
            
            # 메타데이터 저장
            meta_key = f"{cache_key}:meta"
            metadata = {
                "created_at": datetime.now().isoformat(),
                "model": model,
                "temperature": str(temperature),
                "prompt_length": str(len(prompt)),
                "response_length": str(len(response)),
                "hit_count": "0"
            }
            self._redis_client.hset(meta_key, mapping=metadata)
            self._redis_client.expire(meta_key, ttl)
            
            # 캐시 크기 제한 확인
            self._check_cache_size()
            
            logger.debug(f"Cached response for key: {cache_key[:16]}... (TTL: {ttl}s)")
            
        except Exception as e:
            self._error_count += 1
            logger.error(f"Error storing in cache: {e}")
    
    def _check_cache_size(self):
        """캐시 크기 제한 확인 및 정리"""
        try:
            # 캐시 키 개수 확인
            cache_keys = list(self._redis_client.scan_iter(match="llm_cache:*", count=100))
            
            if len(cache_keys) > self._max_size:
                # 가장 오래된 키들 삭제
                keys_to_delete = len(cache_keys) - self._max_size
                
                # TTL이 짧은 순으로 정렬하여 삭제
                keys_with_ttl = []
                for key in cache_keys:
                    if not key.endswith(":meta"):
                        ttl = self._redis_client.ttl(key)
                        if ttl > 0:
                            keys_with_ttl.append((key, ttl))
                
                # TTL이 짧은 순으로 정렬
                keys_with_ttl.sort(key=lambda x: x[1])
                
                # 초과분 삭제
                for key, _ in keys_with_ttl[:keys_to_delete]:
                    self._redis_client.delete(key)
                    self._redis_client.delete(f"{key}:meta")
                
                logger.info(f"Cleaned up {keys_to_delete} cache entries to maintain size limit")
                
        except Exception as e:
            logger.error(f"Error checking cache size: {e}")
    
    def clear(self):
        """전체 캐시 삭제"""
        if not self._enabled or not self._redis_client:
            return
        
        try:
            # LLM 캐시 관련 모든 키 삭제
            keys = list(self._redis_client.scan_iter(match="llm_cache:*"))
            if keys:
                self._redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries")
                
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        stats = {
            "enabled": self._enabled,
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "error_count": self._error_count,
            "hit_rate": 0.0,
            "total_requests": 0,
            "cache_size": 0
        }
        
        total = self._hit_count + self._miss_count
        if total > 0:
            stats["hit_rate"] = (self._hit_count / total) * 100
            stats["total_requests"] = total
        
        if self._enabled and self._redis_client:
            try:
                # 현재 캐시 크기
                cache_keys = list(self._redis_client.scan_iter(match="llm_cache:*", count=100))
                stats["cache_size"] = len([k for k in cache_keys if not k.endswith(":meta")])
            except Exception:
                pass
        
        return stats
    
    def is_available(self) -> bool:
        """캐시 사용 가능 여부 확인"""
        if not self._enabled or not self._redis_client:
            return False
        
        try:
            self._redis_client.ping()
            return True
        except Exception:
            return False


# 전역 LLM 캐시 인스턴스
import os
llm_cache = LLMCache()