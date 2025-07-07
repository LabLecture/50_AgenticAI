"""
Vector store management module using Weaviate with connection pooling.
Handles schema and sample query retrieval for SQL generation.
"""

import weaviate
from langchain_community.embeddings import OllamaEmbeddings
from typing import List, Optional, Dict, Any
import logging
import os

from .config import config
from .vector_store_pool import WeaviateConnectionPool

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Weaviate 벡터 스토어 관리 클래스 (연결 풀링 지원)"""
    
    def __init__(self):
        """벡터 스토어 매니저 초기화"""
        self._connection_pool = None
        self._embeddings = None
        self._use_pool = os.getenv("VECTOR_STORE_USE_POOL", "true").lower() == "true"
        self._direct_client = None  # 풀을 사용하지 않을 때의 직접 연결
        
    def initialize(self):
        """Weaviate 클라이언트 및 임베딩 초기화"""
        # Weaviate가 비활성화된 경우 건너뛰기
        if not config.weaviate.enabled:
            logger.info("Weaviate is disabled via configuration")
            return
            
        try:
            # Ollama 임베딩 초기화
            self._embeddings = OllamaEmbeddings(
                base_url=config.ollama.base_url,
                model=config.ollama.embedding_model
            )
            
            # 연결 풀 사용 여부에 따라 초기화
            if self._use_pool:
                # 연결 풀 초기화
                self._connection_pool = WeaviateConnectionPool(
                    min_connections=int(os.getenv("VECTOR_STORE_MIN_CONNECTIONS", "2")),
                    max_connections=int(os.getenv("VECTOR_STORE_MAX_CONNECTIONS", "10")),
                    connection_lifetime=int(os.getenv("VECTOR_STORE_CONNECTION_LIFETIME", "3600")),
                    health_check_interval=int(os.getenv("VECTOR_STORE_HEALTH_CHECK_INTERVAL", "60"))
                )
                logger.info("Vector store initialized with connection pooling")
            else:
                # 직접 연결 초기화
                self._direct_client = weaviate.connect_to_local(
                    host=config.weaviate.host,
                    port=config.weaviate.port
                )
                logger.info("Vector store initialized with direct connection")
                
        except Exception as e:
            if config.vector_store_optional:
                logger.warning(f"Vector store initialization failed: {e}")
                logger.warning("Vector store will be disabled. Schema examples will be empty.")
                self._connection_pool = None
                self._direct_client = None
                self._embeddings = None
            else:
                logger.error(f"Vector store initialization failed: {e}")
                raise
    
    def _get_client(self):
        """클라이언트 획득 (풀 또는 직접 연결)"""
        if self._use_pool and self._connection_pool:
            return self._connection_pool.get_connection()
        elif self._direct_client:
            from contextlib import contextmanager
            @contextmanager
            def direct_client_context():
                yield self._direct_client
            return direct_client_context()
        else:
            raise RuntimeError("Vector store not initialized")
    
    def search_schema_examples(self, user_query: str, limit: int = 3) -> List[str]:
        """사용자 쿼리에 대한 스키마 예제 검색"""
        if not self._embeddings:
            logger.warning("Embeddings not available, returning empty list")
            return []
        
        try:
            with self._get_client() as client:
                schema_collection = client.collections.get(config.weaviate.schema_collection)
                embedded_query = self._embeddings.embed_query(user_query)
                
                results = schema_collection.query.hybrid(
                    query=user_query,
                    vector=embedded_query,
                    alpha=0.5,
                    limit=limit,
                    return_properties=["query", "type_name", "explanation", "search_content"]
                )
                
                retrieved_examples = []
                for obj in results.objects:
                    sql_example = obj.properties.get("query")
                    if sql_example:
                        retrieved_examples.append(str(sql_example))
                
                logger.info(f"Found {len(retrieved_examples)} schema examples for query: {user_query}")
                return retrieved_examples
                
        except Exception as e:
            logger.error(f"Error searching schema examples: {e}")
            return []
    
    def search_sample_queries(self, user_query: str, limit: int = 2, max_distance: float = 0.5) -> List[str]:
        """사용자 쿼리에 대한 샘플 쿼리 검색"""
        if not self._embeddings:
            logger.warning("Embeddings not available, returning empty list")
            return []
        
        try:
            with self._get_client() as client:
                sample_collection = client.collections.get(config.weaviate.sample_collection)
                embedded_query = self._embeddings.embed_query(user_query)
                
                results = sample_collection.query.hybrid(
                    query=user_query,
                    vector=embedded_query,
                    alpha=0.5,
                    max_vector_distance=max_distance,
                    limit=limit,
                    return_properties=["query", "explanation"]
                )
                
                retrieved_samples = []
                for obj in results.objects:
                    sql_example = obj.properties.get("query")
                    if sql_example:
                        retrieved_samples.append(str(sql_example))
                
                logger.info(f"Found {len(retrieved_samples)} sample queries for query: {user_query}")
                return retrieved_samples
                
        except Exception as e:
            logger.error(f"Error searching sample queries: {e}")
            return []
    
    def get_schema_search_results_message(self, user_query: str, limit: int = 3) -> str:
        """스키마 검색 결과를 메시지 형태로 반환"""
        if not self._embeddings:
            return "Vector DB schema Search Results:\nVector store not available - using basic schema information."
        
        try:
            with self._get_client() as client:
                schema_collection = client.collections.get(config.weaviate.schema_collection)
                embedded_query = self._embeddings.embed_query(user_query)
                
                results = schema_collection.query.hybrid(
                    query=user_query,
                    vector=embedded_query,
                    alpha=0.5,
                    limit=limit,
                    return_properties=["query", "type_name", "explanation", "search_content"]
                )
                
                message_content = "Vector DB schema Search Results:\n"
                if not results.objects:
                    message_content += "No relevant schema found."
                else:
                    for i, obj in enumerate(results.objects):
                        sql_example = obj.properties.get("query")
                        if sql_example:
                            type_name = obj.properties.get("type_name", "N/A")
                            explanation = obj.properties.get("explanation", "N/A")
                            search_content = obj.properties.get("search_content", "N/A")
                            
                            message_content += (
                                f"\n--- Example {i+1} (Type: {type_name}) ---\n"
                                f"Explanation: {explanation}\n"
                                f"Search Content Used (for debugging): {search_content}\n"
                                f"```sql\n{sql_example}\n```"
                            )
                
                return message_content
                
        except Exception as e:
            logger.error(f"Error getting schema search results: {e}")
            return f"Warning: Vector DB query failed. {e}"
    
    def get_sample_search_results_message(self, user_query: str, limit: int = 2) -> str:
        """샘플 쿼리 검색 결과를 메시지 형태로 반환"""
        if not self._embeddings:
            return "Vector DB sample_query Search Results:\nVector store not available - no sample queries available."
        
        try:
            with self._get_client() as client:
                sample_collection = client.collections.get(config.weaviate.sample_collection)
                embedded_query = self._embeddings.embed_query(user_query)
                
                results = sample_collection.query.hybrid(
                    query=user_query,
                    vector=embedded_query,
                    alpha=0.5,
                    max_vector_distance=0.5,
                    limit=limit,
                    return_properties=["query", "explanation"]
                )
                
                message_content = "Vector DB sample_query Search Results:\n"
                if not results.objects:
                    message_content += "No relevant samples found."
                else:
                    for i, obj in enumerate(results.objects):
                        sql_example = obj.properties.get("query")
                        if sql_example:
                            explanation = obj.properties.get("explanation", "N/A")
                            
                            message_content += (
                                f"\n--- Example {i+1} ---\n"
                                f"Explanation: {explanation}\n"
                                f"```sql\n{sql_example}\n```"
                            )
                
                return message_content
                
        except Exception as e:
            logger.error(f"Error getting sample search results: {e}")
            return f"Warning: Vector DB query failed. {e}"
    
    def get_pool_stats(self) -> Optional[Dict[str, Any]]:
        """연결 풀 통계 반환"""
        if self._use_pool and self._connection_pool:
            return self._connection_pool.get_stats()
        return None
    
    def close(self):
        """Weaviate 클라이언트 연결 종료"""
        if self._use_pool and self._connection_pool:
            self._connection_pool.close_all()
            logger.info("Vector store connection pool closed")
        elif self._direct_client:
            self._direct_client.close()
            logger.info("Vector store direct connection closed")


# 전역 벡터 스토어 매니저 인스턴스
vector_store_manager = VectorStoreManager()