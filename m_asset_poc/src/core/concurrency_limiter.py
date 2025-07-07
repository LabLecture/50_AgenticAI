"""
Concurrency limiter module for controlling simultaneous connections.
Implements a semaphore-based approach with request queuing.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
import time
import logging
from datetime import datetime
import os

from .config import config

logger = logging.getLogger(__name__)


class ConcurrencyLimiter:
    """동시 접속자 수 제한 및 대기 큐 관리 클래스"""
    
    def __init__(self, max_concurrent: int = 10, timeout: float = 300.0):
        """
        동시성 제한자 초기화
        
        Args:
            max_concurrent: 최대 동시 접속자 수
            timeout: 대기 큐 타임아웃 (초)
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active_requests = 0
        self._queued_requests = 0
        self._total_requests = 0
        self._request_stats = {}
        self._start_time = time.time()
        
        logger.info(f"Concurrency limiter initialized with max_concurrent={max_concurrent}")
    
    @asynccontextmanager
    async def acquire(self, request_id: Optional[str] = None):
        """
        동시성 제한을 위한 세마포어 획득
        
        Args:
            request_id: 요청 식별자
            
        Raises:
            asyncio.TimeoutError: 대기 시간 초과
        """
        self._total_requests += 1
        self._queued_requests += 1
        
        request_info = {
            "id": request_id or f"req_{self._total_requests}",
            "queued_at": datetime.now(),
            "queue_position": self._queued_requests,
            "active_requests": self._active_requests
        }
        
        logger.info(f"Request {request_info['id']} queued. Position: {request_info['queue_position']}, Active: {self._active_requests}/{self.max_concurrent}")
        
        try:
            # 세마포어 획득 시도 (타임아웃 적용)
            await asyncio.wait_for(
                self._semaphore.acquire(),
                timeout=self.timeout
            )
                
            self._queued_requests -= 1
            self._active_requests += 1
            
            request_info["started_at"] = datetime.now()
            request_info["wait_time"] = (request_info["started_at"] - request_info["queued_at"]).total_seconds()
            
            logger.info(f"Request {request_info['id']} started. Wait time: {request_info['wait_time']:.2f}s, Active: {self._active_requests}/{self.max_concurrent}")
            
            yield request_info
            
        except asyncio.TimeoutError:
            self._queued_requests -= 1
            logger.warning(f"Request {request_info['id']} timed out after {self.timeout}s")
            raise
            
        finally:
            # 세마포어 해제
            if hasattr(self._semaphore, '_value'):
                if self._active_requests > 0:
                    self._active_requests -= 1
                    self._semaphore.release()
                    
                    if "started_at" in request_info:
                        request_info["completed_at"] = datetime.now()
                        request_info["processing_time"] = (request_info["completed_at"] - request_info["started_at"]).total_seconds()
                        
                        logger.info(f"Request {request_info['id']} completed. Processing time: {request_info['processing_time']:.2f}s, Active: {self._active_requests}/{self.max_concurrent}")
    
    def get_status(self) -> Dict[str, Any]:
        """현재 동시성 제한자 상태 반환"""
        return {
            "max_concurrent": self.max_concurrent,
            "active_requests": self._active_requests,
            "queued_requests": self._queued_requests,
            "total_requests": self._total_requests,
            "uptime_seconds": time.time() - self._start_time,
            "average_active": self._active_requests / max((time.time() - self._start_time), 1)
        }
    
    async def wait_for_slot(self) -> bool:
        """
        사용 가능한 슬롯이 있을 때까지 대기
        
        Returns:
            bool: 슬롯 사용 가능 여부
        """
        if self._active_requests < self.max_concurrent:
            return True
            
        # 짧은 시간 대기 후 재시도
        await asyncio.sleep(0.1)
        return self._active_requests < self.max_concurrent
    
    def is_at_capacity(self) -> bool:
        """최대 용량에 도달했는지 확인"""
        return self._active_requests >= self.max_concurrent


# 전역 동시성 제한자 인스턴스
concurrency_limiter = ConcurrencyLimiter(
    max_concurrent=int(os.getenv("MAX_CONCURRENT_REQUESTS", "10")),
    timeout=float(os.getenv("REQUEST_QUEUE_TIMEOUT", "300"))
)