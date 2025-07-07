"""
Vector store management module using Weaviate.
Handles schema and sample query retrieval for SQL generation.
"""

import weaviate
from langchain_community.embeddings import OllamaEmbeddings
from typing import List, Optional, Dict, Any
import logging

from .config import config
from .weaviate_pool import weaviate_pool

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Weaviate 벡터 스토어 관리 클래스"""
    
    def __init__(self):
        """벡터 스토어 매니저 초기화"""
        self._client = None
        self._embeddings = None
        self._schema_collection = None
        self._sample_collection = None
        self._use_pool = False
        
    def initialize(self):
        """Weaviate 클라이언트 및 임베딩 초기화"""
        # Weaviate가 비활성화된 경우 건너뛰기
        if not config.weaviate.enabled:
            logger.info("Weaviate is disabled via configuration")
            return
            
        try:
            # 연결 풀 사용 여부 확인
            self._use_pool = weaviate_pool.enabled
            
            if self._use_pool:
                # 연결 풀 초기화
                weaviate_pool.initialize()
                logger.info("Using Weaviate connection pool")
                
                # 임베딩만 초기화 (연결은 필요할 때 풀에서 가져옴)
                self._embeddings = OllamaEmbeddings(
                    base_url=config.ollama.base_url,
                    model=config.ollama.embedding_model
                )
            else:
                # 기존 방식: 단일 연결 사용
                self._client = weaviate.connect_to_local(
                    host=config.weaviate.host,
                    port=config.weaviate.port
                )
                
                # Ollama 임베딩 초기화
                self._embeddings = OllamaEmbeddings(
                    base_url=config.ollama.base_url,
                    model=config.ollama.embedding_model
                )
                
                # 컬렉션 초기화
                self._schema_collection = self._client.collections.get(config.weaviate.schema_collection)
                self._sample_collection = self._client.collections.get(config.weaviate.sample_collection)
            
            logger.info("Vector store initialized successfully")
            
        except Exception as e:
            if config.vector_store_optional:
                logger.warning(f"Vector store initialization failed: {e}")
                logger.warning("Vector store will be disabled. Schema examples will be empty.")
                self._client = None
                self._embeddings = None
                self._schema_collection = None
                self._sample_collection = None
            else:
                logger.error(f"Vector store initialization failed: {e}")
                raise
    
    def search_schema_examples(self, user_query: str, limit: int = 3) -> List[str]:
        """사용자 쿼리에 대한 스키마 예제 검색"""
        if self._use_pool:
            # 연결 풀 사용
            try:
                embedded_query = self._embeddings.embed_query(user_query)
                
                with weaviate_pool.get_connection() as client:
                    schema_collection = client.collections.get(config.weaviate.schema_collection)
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
        else:
            # 기존 방식
            if self._schema_collection is None:
                if self._client is None:
                    self.initialize()
                
                if self._schema_collection is None:
                    logger.warning("Schema collection not available, returning empty list")
                    return []
            
            try:
                embedded_query = self._embeddings.embed_query(user_query)
                results = self._schema_collection.query.hybrid(
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
        if self._use_pool:
            # 연결 풀 사용
            try:
                embedded_query = self._embeddings.embed_query(user_query)
                
                with weaviate_pool.get_connection() as client:
                    sample_collection = client.collections.get(config.weaviate.sample_collection)
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
        else:
            # 기존 방식
            if self._sample_collection is None:
                if self._client is None:
                    self.initialize()
                
                if self._sample_collection is None:
                    logger.warning("Sample collection not available, returning empty list")
                    return []
            
            try:
                embedded_query = self._embeddings.embed_query(user_query)
                results = self._sample_collection.query.hybrid(
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
        if self._schema_collection is None:
            if self._client is None:
                self.initialize()
            
            if self._schema_collection is None:
                return "Vector DB schema Search Results:\nVector store not available - using basic schema information."
        
        try:
            embedded_query = self._embeddings.embed_query(user_query)
            results = self._schema_collection.query.hybrid(
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
        if self._sample_collection is None:
            if self._client is None:
                self.initialize()
            
            if self._sample_collection is None:
                return "Vector DB sample_query Search Results:\nVector store not available - no sample queries available."
        
        try:
            embedded_query = self._embeddings.embed_query(user_query)
            results = self._sample_collection.query.hybrid(
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
    
    def close(self):
        """Weaviate 클라이언트 연결 종료"""
        if self._use_pool:
            # 연결 풀 종료
            weaviate_pool.shutdown()
            logger.info("Vector store connection pool shut down")
        elif self._client:
            # 단일 연결 종료
            self._client.close()
            logger.info("Vector store connection closed")


# 전역 벡터 스토어 매니저 인스턴스
vector_store_manager = VectorStoreManager()