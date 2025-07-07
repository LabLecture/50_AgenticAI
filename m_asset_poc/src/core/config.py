"""
Configuration module for the M-Asset POC application.
Contains database connection settings, API endpoints, and other configuration values.
"""

import os
from typing import Optional, Any
from urllib.parse import quote_plus
from dotenv import load_dotenv
from datetime import datetime

# 환경 변수 파일 로드
load_dotenv()


class DatabaseConfig:
    """데이터베이스 연결 설정 클래스"""
    
    def __init__(self):
        """데이터베이스 연결 정보 초기화"""
        self.user = os.getenv("DB_USER", "aitheuser1")
        self.password = os.getenv("DB_PASSWORD", "aithepwd8#")
        self.host = os.getenv("DB_HOST", "192.168.1.204")
        self.port = os.getenv("DB_PORT", "55432")
        self.database = os.getenv("DB_NAME", "skku")
        
    @property
    def connection_string(self) -> str:
        """PostgreSQL 연결 문자열 반환"""
        encoded_password = quote_plus(self.password)
        return f"postgresql+psycopg2://{self.user}:{encoded_password}@{self.host}:{self.port}/{self.database}?options=-csearch_path%3Dm_asset"
    
    @property
    def asyncpg_connection_string(self) -> str:
        """AsyncPG 연결 문자열 반환"""
        encoded_password = quote_plus(self.password)
        return f"postgresql://{self.user}:{encoded_password}@{self.host}:{self.port}/{self.database}"


class OllamaConfig:
    """Ollama 서버 설정 클래스"""
    
    def __init__(self):
        """Ollama 서버 연결 정보 초기화"""
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://192.168.1.203:11434")
        self.embedding_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "bge-m3:latest")


class VLLMConfig:
    """VLLM 서버 설정 클래스"""
    
    def __init__(self):
        """VLLM 서버 연결 정보 초기화"""
        self.server_url = os.getenv("VLLM_SERVER_URL", "http://192.168.1.239/vllm9/v1")
        self.model_name = os.getenv("VLLM_MODEL_NAME", "qwencoder-32b")
        self.api_key = os.getenv("VLLM_API_KEY", "EMPTY")
        self.temperature = float(os.getenv("VLLM_TEMPERATURE", "0"))


class WeaviateConfig:
    """Weaviate 벡터 DB 설정 클래스"""
    
    def __init__(self):
        """Weaviate 연결 정보 초기화"""
        self.host = os.getenv("WEAVIATE_HOST", "192.168.1.203")
        self.port = int(os.getenv("WEAVIATE_PORT", "8585"))
        self.schema_collection = os.getenv("WEAVIATE_SCHEMA_COLLECTION", "m_asset_hybrid_1")
        self.sample_collection = os.getenv("WEAVIATE_SAMPLE_COLLECTION", "m_asset_sample_query_2_hint")
        # Weaviate 서버 비활성화 옵션 추가 (기본값: true로 활성화)
        self.enabled = os.getenv("WEAVIATE_ENABLED", "true").lower() == "true"


class LangfuseConfig:
    """Langfuse 추적 시스템 설정 클래스"""
    
    def __init__(self):
        """Langfuse 연결 정보 초기화"""
        self.public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-9432a302-838d-4480-8839-5a8ecdadf9b6")
        self.secret_key = os.getenv("LANGFUSE_SECRET_KEY", "sk-lf-58132035-a6ff-4848-9e96-1dda026f4a83")
        self.host = os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")
        # Langfuse 추적 비활성화 옵션 추가
        self.enabled = os.getenv("LANGFUSE_ENABLED", "true").lower() == "true"


class APIConfig:
    """API 서버 설정 클래스"""
    
    def __init__(self):
        """API 서버 설정 초기화"""
        self.host = os.getenv("API_HOST", "0.0.0.0")
        self.port = int(os.getenv("API_PORT", "8010"))
        self.debug = os.getenv("API_DEBUG", "False").lower() == "true"


class A2AConfig:
    """A2A (Agent-to-Agent) 프로토콜 설정 클래스"""
    
    def __init__(self):
        """A2A 설정 초기화"""
        self.enabled = os.getenv("A2A_ENABLED", "false").lower() == "true"
        self.base_url = os.getenv("A2A_BASE_URL", "http://localhost:8010")
        self.auth_token = os.getenv("A2A_AUTH_TOKEN")
        
        # Agent Card 정보
        self.agent_name = os.getenv("A2A_AGENT_NAME", "M-Asset Text2SQL Agent")
        self.agent_description = os.getenv("A2A_AGENT_DESCRIPTION", "한국 증권 데이터에 대한 자연어 질의를 SQL로 변환하고 실행하는 에이전트")
        self.agent_version = os.getenv("A2A_AGENT_VERSION", "1.0.0")
        
        # 기능 설정
        self.streaming_enabled = os.getenv("A2A_STREAMING_ENABLED", "true").lower() == "true"
        self.push_notifications_enabled = os.getenv("A2A_PUSH_NOTIFICATIONS_ENABLED", "false").lower() == "true"
        self.state_history_enabled = os.getenv("A2A_STATE_HISTORY_ENABLED", "true").lower() == "true"


class AppConfig:
    """애플리케이션 전체 설정 클래스"""
    
    def __init__(self):
        """전체 설정 초기화"""
        self.database = DatabaseConfig()
        self.ollama = OllamaConfig()
        self.vllm = VLLMConfig()
        self.weaviate = WeaviateConfig()
        self.langfuse = LangfuseConfig()
        self.api = APIConfig()
        self.a2a = A2AConfig()
        
        # 최대 재시도 횟수
        self.max_text_to_sql_retries = int(os.getenv("MAX_TEXT_TO_SQL_RETRIES", "3"))
        
        # 벡터 스토어 없이 실행하는 모드
        self.vector_store_optional = os.getenv("VECTOR_STORE_OPTIONAL", "true").lower() == "true"
    
    def get(self, key: str, default: Any = None) -> Any:
        """환경 변수 가져오기 헬퍼 메서드"""
        return os.getenv(key, default)
    
    def get_current_time(self) -> datetime:
        """현재 시간 반환"""
        return datetime.now()


# 전역 설정 인스턴스
config = AppConfig()