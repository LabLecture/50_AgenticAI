"""
Database connection and management module.
Handles both synchronous and asynchronous database connections.
"""

import asyncpg
import psycopg2
from sqlalchemy import create_engine
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from typing import Optional, Any, List, Tuple
import logging

from .config import config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """데이터베이스 연결 및 관리 클래스"""
    
    def __init__(self):
        """데이터베이스 매니저 초기화"""
        self._engine = None
        self._sql_db = None
        self._toolkit = None
        self._async_pool = None
        
    def initialize_sync_db(self) -> SQLDatabase:
        """동기식 데이터베이스 연결 초기화"""
        try:
            self._engine = create_engine(config.database.connection_string, echo=False)
            self._sql_db = SQLDatabase(engine=self._engine)
            logger.info(f"DB Connected. Dialect: {self._sql_db.dialect}. Tables: {self._sql_db.get_usable_table_names()}")
            return self._sql_db
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    async def initialize_async_db(self) -> asyncpg.Pool:
        """비동기식 데이터베이스 연결 풀 초기화"""
        try:
            self._async_pool = await asyncpg.create_pool(
                config.database.asyncpg_connection_string,
                min_size=1,
                max_size=10,
                server_settings={'search_path': 'm_asset'}
            )
            logger.info("Async database pool initialized successfully")
            return self._async_pool
        except Exception as e:
            logger.error(f"Error creating async database pool: {e}")
            raise
    
    def get_sql_toolkit(self, llm) -> SQLDatabaseToolkit:
        """SQL 툴킷 반환"""
        if self._sql_db is None:
            self.initialize_sync_db()
        
        if self._toolkit is None:
            self._toolkit = SQLDatabaseToolkit(db=self._sql_db, llm=llm)
        
        return self._toolkit
    
    def execute_sync_query(self, query: str) -> List[Tuple]:
        """동기식 쿼리 실행"""
        conn = None
        cur = None
        try:
            conn = psycopg2.connect(
                host=config.database.host,
                dbname=config.database.database,
                user=config.database.user,
                password=config.database.password,
                port=config.database.port
            )
            cur = conn.cursor()
            cur.execute(query)
            result = cur.fetchall()
            logger.info(f"Query executed successfully. Rows returned: {len(result)}")
            return result
        except Exception as e:
            logger.error(f"Error executing sync query: {e}")
            raise
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
    
    async def execute_async_query(self, query: str) -> List[Tuple]:
        """비동기식 쿼리 실행"""
        if self._async_pool is None:
            await self.initialize_async_db()
        
        try:
            async with self._async_pool.acquire() as connection:
                # m_asset 스키마를 기본 검색 경로로 설정
                await connection.execute("SET search_path TO m_asset")
                result = await connection.fetch(query)
                logger.info(f"Async query executed successfully. Rows returned: {len(result)}")
                return result
        except Exception as e:
            logger.error(f"Error executing async query: {e}")
            raise
    
    async def close_async_pool(self):
        """비동기 연결 풀 종료"""
        if self._async_pool:
            await self._async_pool.close()
            logger.info("Async database pool closed")
    
    @property
    def sql_db(self) -> Optional[SQLDatabase]:
        """SQLDatabase 인스턴스 반환"""
        return self._sql_db
    
    @property
    def engine(self):
        """SQLAlchemy Engine 반환"""
        return self._engine


# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager()