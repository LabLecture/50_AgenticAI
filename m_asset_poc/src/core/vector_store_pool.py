"""
Vector store connection pooling module.
Manages Weaviate client connections with pooling support.
"""

import weaviate
from weaviate import Client
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import threading
import time
import queue
import logging
from datetime import datetime

from .config import config

logger = logging.getLogger(__name__)


class WeaviateConnectionPool:
    """Weaviate 연결 풀 관리 클래스"""
    
    def __init__(self, 
                 min_connections: int = 2,
                 max_connections: int = 10,
                 connection_lifetime: int = 3600,
                 health_check_interval: int = 60):
        """
        Weaviate 연결 풀 초기화
        
        Args:
            min_connections: 최소 연결 수
            max_connections: 최대 연결 수
            connection_lifetime: 연결 수명 (초)
            health_check_interval: 헬스 체크 간격 (초)
        """
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connection_lifetime = connection_lifetime
        self.health_check_interval = health_check_interval
        
        self._pool = queue.Queue(maxsize=max_connections)
        self._all_connections = []
        self._lock = threading.Lock()
        self._active_connections = 0
        self._total_connections_created = 0
        self._connection_errors = 0
        self._last_health_check = time.time()
        
        # 풀 초기화
        self._initialize_pool()
        
    def _initialize_pool(self):
        """연결 풀 초기화"""
        logger.info(f"Initializing Weaviate connection pool with min={self.min_connections}, max={self.max_connections}")
        
        # 최소 연결 수만큼 생성
        for _ in range(self.min_connections):
            conn = self._create_connection()
            if conn:
                self._pool.put(conn)
    
    def _create_connection(self) -> Optional[Dict[str, Any]]:
        """새로운 Weaviate 연결 생성"""
        try:
            client = weaviate.connect_to_local(
                host=config.weaviate.host,
                port=config.weaviate.port
            )
            
            connection_info = {
                "client": client,
                "created_at": time.time(),
                "last_used": time.time(),
                "usage_count": 0,
                "id": self._total_connections_created
            }
            
            self._total_connections_created += 1
            
            with self._lock:
                self._all_connections.append(connection_info)
            
            logger.debug(f"Created new Weaviate connection #{connection_info['id']}")
            return connection_info
            
        except Exception as e:
            self._connection_errors += 1
            logger.error(f"Failed to create Weaviate connection: {e}")
            return None
    
    @contextmanager
    def get_connection(self, timeout: float = 30.0):
        """
        연결 풀에서 연결 획득
        
        Args:
            timeout: 연결 대기 시간 제한 (초)
            
        Yields:
            Client: Weaviate 클라이언트
        """
        connection_info = None
        start_time = time.time()
        
        try:
            # 풀에서 연결 획득 시도
            while True:
                try:
                    connection_info = self._pool.get(timeout=1.0)
                    break
                except queue.Empty:
                    # 타임아웃 확인
                    if time.time() - start_time > timeout:
                        raise TimeoutError(f"Failed to acquire connection within {timeout}s")
                    
                    # 풀이 비어있고 최대 연결 수에 도달하지 않았으면 새 연결 생성
                    with self._lock:
                        if len(self._all_connections) < self.max_connections:
                            new_conn = self._create_connection()
                            if new_conn:
                                connection_info = new_conn
                                break
            
            # 연결 수명 확인
            if time.time() - connection_info["created_at"] > self.connection_lifetime:
                logger.debug(f"Connection #{connection_info['id']} exceeded lifetime, recreating")
                connection_info["client"].close()
                
                # 새 연결 생성
                new_conn = self._create_connection()
                if new_conn:
                    connection_info = new_conn
                else:
                    raise Exception("Failed to recreate expired connection")
            
            # 연결 사용 정보 업데이트
            connection_info["last_used"] = time.time()
            connection_info["usage_count"] += 1
            
            with self._lock:
                self._active_connections += 1
            
            # 헬스 체크 수행 (주기적으로)
            if time.time() - self._last_health_check > self.health_check_interval:
                self._perform_health_check()
            
            yield connection_info["client"]
            
        except Exception as e:
            logger.error(f"Error acquiring connection from pool: {e}")
            raise
            
        finally:
            # 연결을 풀에 반환
            if connection_info:
                with self._lock:
                    self._active_connections -= 1
                
                # 연결이 정상이면 풀에 반환
                try:
                    if connection_info["client"].is_ready():
                        self._pool.put(connection_info)
                    else:
                        # 연결이 끊어진 경우 제거
                        with self._lock:
                            self._all_connections.remove(connection_info)
                        connection_info["client"].close()
                        logger.warning(f"Removed unhealthy connection #{connection_info['id']}")
                except Exception:
                    # 연결 상태 확인 실패 시 제거
                    with self._lock:
                        if connection_info in self._all_connections:
                            self._all_connections.remove(connection_info)
    
    def _perform_health_check(self):
        """모든 연결에 대한 헬스 체크 수행"""
        self._last_health_check = time.time()
        
        with self._lock:
            unhealthy_connections = []
            
            for conn_info in self._all_connections:
                try:
                    if not conn_info["client"].is_ready():
                        unhealthy_connections.append(conn_info)
                except Exception:
                    unhealthy_connections.append(conn_info)
            
            # 비정상 연결 제거
            for conn_info in unhealthy_connections:
                self._all_connections.remove(conn_info)
                try:
                    conn_info["client"].close()
                except Exception:
                    pass
                logger.warning(f"Removed unhealthy connection #{conn_info['id']} during health check")
            
            # 최소 연결 수 유지
            current_count = len(self._all_connections)
            if current_count < self.min_connections:
                for _ in range(self.min_connections - current_count):
                    new_conn = self._create_connection()
                    if new_conn:
                        self._pool.put(new_conn)
    
    def get_stats(self) -> Dict[str, Any]:
        """연결 풀 통계 반환"""
        with self._lock:
            pool_size = self._pool.qsize()
            total_connections = len(self._all_connections)
            
        return {
            "pool_size": pool_size,
            "active_connections": self._active_connections,
            "total_connections": total_connections,
            "total_created": self._total_connections_created,
            "connection_errors": self._connection_errors,
            "min_connections": self.min_connections,
            "max_connections": self.max_connections,
            "utilization": (self._active_connections / self.max_connections) * 100 if self.max_connections > 0 else 0
        }
    
    def close_all(self):
        """모든 연결 종료"""
        logger.info("Closing all connections in pool")
        
        with self._lock:
            # 풀에 있는 연결 모두 가져오기
            connections_to_close = []
            while not self._pool.empty():
                try:
                    conn_info = self._pool.get_nowait()
                    connections_to_close.append(conn_info)
                except queue.Empty:
                    break
            
            # 모든 연결 종료
            for conn_info in self._all_connections:
                try:
                    conn_info["client"].close()
                    logger.debug(f"Closed connection #{conn_info['id']}")
                except Exception as e:
                    logger.error(f"Error closing connection #{conn_info['id']}: {e}")
            
            self._all_connections.clear()
            self._active_connections = 0
        
        logger.info("All connections closed")