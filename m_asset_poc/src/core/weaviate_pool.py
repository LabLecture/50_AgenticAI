"""
Weaviate 연결 풀 관리자
동시 요청을 효율적으로 처리하기 위한 연결 풀 구현
"""

import os
import time
import threading
import queue
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from datetime import datetime, timedelta
import weaviate
from weaviate.exceptions import WeaviateConnectionError

logger = logging.getLogger(__name__)


class WeaviateConnection:
    """Weaviate 연결 래퍼"""
    
    def __init__(self, host: str, port: int, connection_id: int):
        """연결 초기화"""
        self.host = host
        self.port = port
        self.connection_id = connection_id
        self.client = None
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        self.in_use = False
        self._lock = threading.Lock()
        
    def connect(self):
        """Weaviate 연결 생성"""
        try:
            self.client = weaviate.connect_to_local(
                host=self.host,
                port=self.port
            )
            logger.info(f"Weaviate connection {self.connection_id} established")
            return True
        except Exception as e:
            logger.error(f"Failed to create connection {self.connection_id}: {e}")
            return False
    
    def is_alive(self) -> bool:
        """연결 상태 확인"""
        if not self.client:
            return False
        
        try:
            # 간단한 health check
            self.client.is_ready()
            return True
        except:
            return False
    
    def close(self):
        """연결 종료"""
        if self.client:
            try:
                self.client.close()
                logger.info(f"Weaviate connection {self.connection_id} closed")
            except Exception as e:
                logger.error(f"Error closing connection {self.connection_id}: {e}")
            finally:
                self.client = None


class WeaviateConnectionPool:
    """Weaviate 연결 풀"""
    
    def __init__(self):
        """연결 풀 초기화"""
        # 환경 변수에서 설정 읽기
        self.enabled = os.getenv("VECTOR_STORE_USE_POOL", "true").lower() == "true"
        self.host = os.getenv("WEAVIATE_HOST", "localhost")
        self.port = int(os.getenv("WEAVIATE_PORT", "8080"))
        self.min_connections = int(os.getenv("VECTOR_STORE_MIN_CONNECTIONS", "2"))
        self.max_connections = int(os.getenv("VECTOR_STORE_MAX_CONNECTIONS", "10"))
        self.connection_lifetime = int(os.getenv("VECTOR_STORE_CONNECTION_LIFETIME", "3600"))
        self.health_check_interval = int(os.getenv("VECTOR_STORE_HEALTH_CHECK_INTERVAL", "60"))
        
        # 내부 상태
        self._connections = []
        self._available_connections = queue.Queue()
        self._lock = threading.Lock()
        self._connection_counter = 0
        self._last_health_check = datetime.now()
        self._initialized = False
        self._shutdown = False
        
        # 통계
        self._stats = {
            "total_connections_created": 0,
            "total_connections_closed": 0,
            "current_active": 0,
            "current_idle": 0,
            "total_requests": 0,
            "total_wait_time": 0.0,
            "health_check_failures": 0
        }
    
    def initialize(self):
        """연결 풀 초기화"""
        if not self.enabled:
            logger.info("Weaviate connection pooling is disabled")
            return
        
        if self._initialized:
            logger.warning("Connection pool already initialized")
            return
        
        logger.info(f"Initializing Weaviate connection pool (min={self.min_connections}, max={self.max_connections})")
        
        # 최소 연결 수만큼 생성
        for i in range(self.min_connections):
            conn = self._create_connection()
            if conn:
                self._available_connections.put(conn)
        
        self._initialized = True
        logger.info(f"Weaviate connection pool initialized with {len(self._connections)} connections")
    
    def _create_connection(self) -> Optional[WeaviateConnection]:
        """새 연결 생성"""
        with self._lock:
            if len(self._connections) >= self.max_connections:
                logger.warning("Maximum connections reached")
                return None
            
            self._connection_counter += 1
            conn = WeaviateConnection(self.host, self.port, self._connection_counter)
            
            if conn.connect():
                self._connections.append(conn)
                self._stats["total_connections_created"] += 1
                return conn
            else:
                return None
    
    @contextmanager
    def get_connection(self, timeout: float = 30.0):
        """연결 풀에서 연결 가져오기 (컨텍스트 매니저)"""
        if not self.enabled:
            # 풀링이 비활성화된 경우 임시 연결 생성
            conn = WeaviateConnection(self.host, self.port, 0)
            if conn.connect():
                try:
                    yield conn.client
                finally:
                    conn.close()
            else:
                raise WeaviateConnectionError("Failed to create connection")
            return
        
        start_time = time.time()
        connection = None
        
        try:
            # 연결 가져오기
            while True:
                try:
                    # 사용 가능한 연결 확인
                    connection = self._available_connections.get(timeout=1.0)
                    
                    # 연결 상태 확인
                    if connection.is_alive():
                        break
                    else:
                        # 죽은 연결은 제거하고 새로 생성
                        logger.warning(f"Dead connection {connection.connection_id} detected")
                        self._remove_connection(connection)
                        connection = self._create_connection()
                        if connection:
                            break
                    
                except queue.Empty:
                    # 새 연결 생성 시도
                    if len(self._connections) < self.max_connections:
                        connection = self._create_connection()
                        if connection:
                            break
                    
                    # 타임아웃 확인
                    if time.time() - start_time > timeout:
                        raise TimeoutError(f"Failed to get connection within {timeout} seconds")
                    
                    # 헬스 체크 수행
                    self._perform_health_check()
            
            # 연결 사용 표시
            connection.in_use = True
            connection.last_used = datetime.now()
            self._stats["total_requests"] += 1
            self._stats["total_wait_time"] += time.time() - start_time
            
            yield connection.client
            
        finally:
            # 연결 반환
            if connection:
                connection.in_use = False
                connection.last_used = datetime.now()
                
                # 연결 수명 확인
                age = (datetime.now() - connection.created_at).total_seconds()
                if age > self.connection_lifetime:
                    logger.info(f"Connection {connection.connection_id} exceeded lifetime, closing")
                    self._remove_connection(connection)
                else:
                    self._available_connections.put(connection)
    
    def _remove_connection(self, connection: WeaviateConnection):
        """연결 제거"""
        with self._lock:
            if connection in self._connections:
                self._connections.remove(connection)
                connection.close()
                self._stats["total_connections_closed"] += 1
    
    def _perform_health_check(self):
        """연결 헬스 체크"""
        now = datetime.now()
        if (now - self._last_health_check).total_seconds() < self.health_check_interval:
            return
        
        self._last_health_check = now
        logger.debug("Performing connection health check")
        
        with self._lock:
            for conn in self._connections[:]:  # 복사본으로 순회
                if not conn.in_use and not conn.is_alive():
                    logger.warning(f"Removing dead connection {conn.connection_id}")
                    self._connections.remove(conn)
                    self._stats["health_check_failures"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """연결 풀 통계 반환"""
        with self._lock:
            active = sum(1 for c in self._connections if c.in_use)
            idle = len(self._connections) - active
            
            self._stats["current_active"] = active
            self._stats["current_idle"] = idle
            
            return {
                **self._stats,
                "enabled": self.enabled,
                "total_connections": len(self._connections),
                "available_connections": self._available_connections.qsize(),
                "avg_wait_time": self._stats["total_wait_time"] / max(1, self._stats["total_requests"])
            }
    
    def shutdown(self):
        """연결 풀 종료"""
        if self._shutdown:
            return
        
        logger.info("Shutting down Weaviate connection pool")
        self._shutdown = True
        
        # 모든 연결 종료
        with self._lock:
            for conn in self._connections:
                conn.close()
            self._connections.clear()
        
        # 큐 비우기
        while not self._available_connections.empty():
            try:
                self._available_connections.get_nowait()
            except queue.Empty:
                break
        
        logger.info("Weaviate connection pool shut down")


# 전역 연결 풀 인스턴스
weaviate_pool = WeaviateConnectionPool()