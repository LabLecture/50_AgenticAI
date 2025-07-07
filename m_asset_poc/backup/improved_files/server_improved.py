"""
FastAPI server for the M-Asset POC application with concurrency control.
Provides REST API endpoints for Text-to-SQL queries with limited concurrent connections.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
import uvicorn
import asyncio
from contextlib import asynccontextmanager

from ..core.config import config
from ..agents.text_to_sql_agent import text_to_sql_agent
from ..core.langfuse_manager import langfuse_manager
from ..core.database import db_manager
from ..core.vector_store import vector_store_manager
from ..core.concurrency_limiter import concurrency_limiter

# 로깅 설정 (가장 먼저 설정)
from ..utils.logging_config import setup_logging, get_log_config_from_env, get_logger, setup_uvicorn_logging

# 환경 변수에서 로그 설정 읽기
log_config = get_log_config_from_env()
setup_logging(**log_config)
logger = get_logger(__name__)

# A2A 통합 (조건부 import)
a2a_agent = None
if config.a2a.enabled:
    try:
        from ..a2a.text2sql_agent import Text2SQLAgent
        a2a_agent = Text2SQLAgent(config.a2a)
        logger.info("A2A Text2SQL Agent initialized successfully")
    except ImportError as e:
        logger.warning(f"A2A SDK not available: {e}. A2A functionality will be disabled.")
    except Exception as e:
        logger.error(f"Failed to initialize A2A agent: {e}")
else:
    logger.info("A2A functionality is disabled")


# 요청/응답 모델 정의
class QueryRequest(BaseModel):
    """쿼리 요청 모델"""
    query: str = Field(..., description="자연어 쿼리")
    session_id: Optional[str] = Field(None, description="세션 ID")
    user_id: Optional[str] = Field(None, description="사용자 ID")


class QueryResponse(BaseModel):
    """쿼리 응답 모델"""
    success: bool = Field(..., description="성공 여부")
    query: str = Field(..., description="입력된 자연어 쿼리")
    generated_sql: Optional[str] = Field(None, description="생성된 SQL 쿼리")
    result: Optional[Any] = Field(None, description="쿼리 실행 결과")
    error_message: Optional[str] = Field(None, description="오류 메시지")
    session_id: Optional[str] = Field(None, description="세션 ID")
    user_id: Optional[str] = Field(None, description="사용자 ID")
    wait_time: Optional[float] = Field(None, description="대기 시간 (초)")


class HealthResponse(BaseModel):
    """헬스 체크 응답 모델"""
    status: str = Field(..., description="서비스 상태")
    version: str = Field(..., description="API 버전")
    components: Dict[str, str] = Field(..., description="구성 요소 상태")


class ConcurrencyStatusResponse(BaseModel):
    """동시성 상태 응답 모델"""
    max_concurrent: int = Field(..., description="최대 동시 접속자 수")
    active_requests: int = Field(..., description="현재 활성 요청 수")
    queued_requests: int = Field(..., description="대기 중인 요청 수")
    total_requests: int = Field(..., description="총 요청 수")
    utilization_percent: float = Field(..., description="활용률 (%)")


# 애플리케이션 시작/종료 시 실행될 함수들
@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 실행
    logger.info("Starting M-Asset POC API Server...")
    
    try:
        # 비동기 데이터베이스 풀 초기화
        await db_manager.initialize_async_db()
        logger.info("Database initialized successfully")
        
        # Langfuse 초기화
        langfuse_manager.initialize()
        logger.info("Langfuse initialized successfully")
        
        # 벡터 스토어 초기화 (실패해도 계속 진행)
        try:
            vector_store_manager.initialize()
            logger.info("Vector store initialized successfully")
        except Exception as e:
            logger.warning(f"Vector store initialization failed: {e}")
            logger.warning("Continuing without vector store - schema examples will be unavailable")
        
        logger.info("All components initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise
    
    yield
    
    # 종료 시 실행
    logger.info("Shutting down M-Asset POC API Server...")
    
    try:
        # 비동기 데이터베이스 풀 종료
        await db_manager.close_async_pool()
        logger.info("Database pool closed")
        
        # Langfuse 플러시
        langfuse_manager.flush()
        logger.info("Langfuse flushed")
        
        # 벡터 스토어 종료
        vector_store_manager.close()
        logger.info("Vector store closed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# FastAPI 애플리케이션 생성
app = FastAPI(
    title="M-Asset POC API",
    description="증권 종목 에이전트 POC API 서버",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=Dict[str, str])
async def root():
    """루트 엔드포인트"""
    return {
        "message": "M-Asset POC API Server",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스 체크 엔드포인트"""
    components = {}
    
    try:
        # 데이터베이스 상태 확인
        if db_manager.sql_db:
            components["database"] = "healthy"
        else:
            components["database"] = "not_initialized"
    except Exception:
        components["database"] = "error"
    
    try:
        # 벡터 스토어 상태 확인
        if vector_store_manager._client:
            components["vector_store"] = "healthy"
        else:
            components["vector_store"] = "not_initialized"
    except Exception:
        components["vector_store"] = "error"
    
    try:
        # Langfuse 상태 확인
        if langfuse_manager._langfuse:
            components["langfuse"] = "healthy"
        else:
            components["langfuse"] = "not_initialized"
    except Exception:
        components["langfuse"] = "error"
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        components=components
    )


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    자연어 쿼리를 SQL로 변환하고 실행 (동시성 제한 적용)
    
    Args:
        request: 쿼리 요청 데이터
        
    Returns:
        QueryResponse: 쿼리 처리 결과
    """
    logger.info(f"Received query: {request.query}")
    
    # 동시성 제한 상태 로깅
    if concurrency_limiter.is_at_capacity():
        logger.warning(f"Server at capacity. Current status: {concurrency_limiter.get_status()}")
    
    try:
        # 동시성 제한 적용
        async with concurrency_limiter.acquire(
            request_id=f"{request.session_id or 'anonymous'}_{request.user_id or 'user'}"
        ) as req_info:
            wait_time = req_info.get('wait_time', 0)
            logger.info(f"Processing request after {wait_time:.2f}s wait")
            
            # Text-to-SQL 에이전트로 쿼리 처리 (동기 함수를 비동기로 실행)
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                text_to_sql_agent.query,
                request.query,
                request.session_id,
                request.user_id
            )
            
            # 결과에서 필요한 정보 추출
            final_query = result.get("final_query", "")
            query_result = result.get("query_result", "")
            error_message = result.get("error_message")
            final_answer = result.get("final_answer")
            
            # 성공 여부 판단
            success = error_message is None and final_query and query_result is not None
            
            logger.info(f"Query processed successfully: {success}")
            logger.debug(f"Query result type: {type(query_result)}, value: {query_result}")
            
            # final_answer가 있으면 그것을 반환하고, 없으면 query_result를 반환
            display_result = final_answer if final_answer else query_result
            
            return QueryResponse(
                success=success,
                query=request.query,
                generated_sql=final_query if final_query else None,
                result=display_result if success else None,
                error_message=error_message,
                session_id=request.session_id,
                user_id=request.user_id,
                wait_time=wait_time
            )
    
    except asyncio.TimeoutError:
        logger.error("Request timed out in queue")
        return QueryResponse(
            success=False,
            query=request.query,
            generated_sql=None,
            result=None,
            error_message="Request timed out. Server is too busy. Please try again later.",
            session_id=request.session_id,
            user_id=request.user_id
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        
        return QueryResponse(
            success=False,
            query=request.query,
            generated_sql=None,
            result=None,
            error_message=f"Internal server error: {str(e)}",
            session_id=request.session_id,
            user_id=request.user_id
        )


@app.post("/query/async")
async def process_query_async(request: QueryRequest, background_tasks: BackgroundTasks):
    """
    비동기 쿼리 처리 (백그라운드 작업)
    
    Args:
        request: 쿼리 요청 데이터
        background_tasks: FastAPI 백그라운드 태스크
        
    Returns:
        Dict: 작업 접수 확인
    """
    logger.info(f"Received async query: {request.query}")
    
    # 동시성 제한 확인 (백그라운드 작업도 제한)
    if concurrency_limiter.is_at_capacity():
        logger.warning("Cannot accept background task - server at capacity")
        return {
            "message": "Server at capacity. Please try again later.",
            "accepted": False,
            "query": request.query,
            "concurrency_status": concurrency_limiter.get_status()
        }
    
    def process_in_background():
        """백그라운드에서 쿼리 처리"""
        try:
            result = text_to_sql_agent.query(
                user_query=request.query,
                session_id=request.session_id,
                user_id=request.user_id
            )
            logger.info("Background query processing completed")
        except Exception as e:
            logger.error(f"Error in background query processing: {e}")
    
    background_tasks.add_task(process_in_background)
    
    return {
        "message": "Query submitted for background processing",
        "accepted": True,
        "query": request.query,
        "session_id": request.session_id,
        "user_id": request.user_id
    }


@app.get("/concurrency/status", response_model=ConcurrencyStatusResponse)
async def get_concurrency_status():
    """동시성 제한자 상태 조회"""
    status = concurrency_limiter.get_status()
    
    return ConcurrencyStatusResponse(
        max_concurrent=status["max_concurrent"],
        active_requests=status["active_requests"],
        queued_requests=status["queued_requests"],
        total_requests=status["total_requests"],
        utilization_percent=(status["active_requests"] / status["max_concurrent"]) * 100
    )


@app.get("/status")
async def get_system_status():
    """시스템 상태 정보 조회"""
    try:
        # 데이터베이스 테이블 정보
        tables = []
        if db_manager.sql_db:
            tables = db_manager.sql_db.get_usable_table_names()
        
        return {
            "system": "M-Asset POC",
            "status": "running",
            "config": {
                "api_port": config.api.port,
                "database_host": config.database.host,
                "database_port": config.database.port,
                "weaviate_host": config.weaviate.host,
                "weaviate_port": config.weaviate.port,
                "ollama_host": config.ollama.base_url,
                "max_retries": config.max_text_to_sql_retries
            },
            "database": {
                "connected": db_manager.sql_db is not None,
                "tables_count": len(tables),
                "tables": tables
            },
            "langfuse": {
                "enabled": langfuse_manager._langfuse is not None,
                "session_id": langfuse_manager.session_id,
                "user_id": langfuse_manager.user_id
            },
            "concurrency": concurrency_limiter.get_status()
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting system status: {str(e)}")


# A2A 엔드포인트
@app.get("/.well-known/agent.json")
async def get_agent_card():
    """A2A Agent Card 반환"""
    if not a2a_agent or not a2a_agent.is_available():
        raise HTTPException(status_code=404, detail="A2A functionality not available")
    
    agent_card = a2a_agent.get_agent_card()
    if not agent_card:
        raise HTTPException(status_code=500, detail="Agent card not available")
    
    return agent_card


@app.get("/a2a/status")
async def get_a2a_status():
    """A2A 에이전트 상태 확인"""
    return {
        "a2a_enabled": config.a2a.enabled,
        "a2a_available": a2a_agent is not None and a2a_agent.is_available(),
        "agent_name": config.a2a.agent_name if a2a_agent else None,
        "streaming_enabled": config.a2a.streaming_enabled if a2a_agent else False
    }


if __name__ == "__main__":
    """서버 직접 실행 시"""
    logger.info(f"Starting server on {config.api.host}:{config.api.port}")
    
    uvicorn.run(
        "src.api.server:app",
        host=config.api.host,
        port=config.api.port,
        reload=config.api.debug,
        log_level="info"
    )