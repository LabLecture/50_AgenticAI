"""
Langfuse integration module for tracing and monitoring.
Handles session management and callback setup.
"""

from typing import Optional, Any
import logging
import uuid

from .config import config

# langfuse는 필요할 때만 import
try:
    from langfuse import Langfuse
    from langfuse.langchain import CallbackHandler
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    # 타입 힌트를 위한 더미 클래스
    CallbackHandler = Any

logger = logging.getLogger(__name__)


class LangfuseManager:
    """Langfuse 추적 시스템 관리 클래스"""
    
    def __init__(self):
        """Langfuse 매니저 초기화"""
        self._langfuse = None
        self._callback_handler = None
        self._session_id = None
        self._user_id = None
        
    def initialize(self, session_id: Optional[str] = None, user_id: Optional[str] = None):
        """Langfuse 클라이언트 및 콜백 핸들러 초기화"""
        # Langfuse가 비활성화된 경우 건너뛰기
        if not config.langfuse.enabled:
            logger.info("Langfuse is disabled via configuration")
            return
            
        # Langfuse 라이브러리가 없는 경우 건너뛰기
        if not LANGFUSE_AVAILABLE:
            logger.warning("Langfuse library not available - tracing will be disabled")
            return
            
        try:
            self._langfuse = Langfuse(
                public_key=config.langfuse.public_key,
                secret_key=config.langfuse.secret_key,
                host=config.langfuse.host
            )
            
            # 세션 ID와 사용자 ID 설정
            self._session_id = session_id or str(uuid.uuid4())
            self._user_id = user_id or "anonymous"
            
            # 콜백 핸들러 초기화 (session_id, user_id 직접 설정)
            try:
                # 최신 Langfuse에서는 다양한 방법으로 세션 정보 설정 시도
                self._callback_handler = CallbackHandler(
                    session_id=self._session_id,
                    user_id=self._user_id
                )
            except TypeError:
                # session_id, user_id 파라미터가 지원되지 않는 경우
                try:
                    self._callback_handler = CallbackHandler(
                        user_id=self._user_id
                    )
                except TypeError:
                    # 기본 생성자 사용
                    self._callback_handler = CallbackHandler()
            
            logger.info(f"Langfuse initialized - Session ID: {self._session_id}, User ID: {self._user_id}")
            
        except Exception as e:
            logger.error(f"Error initializing Langfuse: {e}")
            raise
    
    def get_callback_handler(self) -> Optional[CallbackHandler]:
        """콜백 핸들러 반환"""
        if self._callback_handler is None:
            self.initialize()
        
        # CallbackHandler에 현재 세션 정보 설정
        if self._callback_handler and hasattr(self._callback_handler, 'langfuse'):
            try:
                # CallbackHandler의 내부 Langfuse 인스턴스에 세션 정보 설정
                if hasattr(self._callback_handler.langfuse, 'session_id'):
                    self._callback_handler.langfuse.session_id = self._session_id
                if hasattr(self._callback_handler.langfuse, 'user_id'):
                    self._callback_handler.langfuse.user_id = self._user_id
            except Exception as e:
                logger.debug(f"Could not set session info on callback handler: {e}")
                
        return self._callback_handler
    
    def create_user_and_session(self, user_id: str, session_id: str):
        """사용자와 세션 정보 설정 (Langfuse 3.x에서는 trace 생성 시 자동으로 처리됨)"""
        if self._langfuse is None:
            self.initialize()
        
        # Langfuse 3.x에서는 사용자와 세션이 trace 생성 시 자동으로 관리됨
        # 별도의 create_user/create_session 메서드가 없음
        logger.info(f"User and session IDs set for tracing: {user_id}, {session_id}")
        return True

    def create_trace(self, name: str, input_data: dict = None, metadata: dict = None):
        """새로운 추적 생성 (Langfuse 3.x에서는 CallbackHandler가 자동으로 처리)"""
        if self._langfuse is None:
            self.initialize()
        
        # Langfuse 3.x에서는 trace가 CallbackHandler를 통해 자동으로 생성됨
        # 별도의 manual trace 생성이 필요하지 않음
        logger.debug(f"Trace will be created automatically via CallbackHandler: {name}")
        return None
    
    def update_session(self, session_id: str, user_id: Optional[str] = None):
        """세션 ID와 사용자 ID 업데이트"""
        self._session_id = session_id
        if user_id:
            self._user_id = user_id
        
        # 콜백 핸들러 재초기화 (session_id, user_id 직접 설정)
        if LANGFUSE_AVAILABLE:
            try:
                self._callback_handler = CallbackHandler(
                    session_id=self._session_id,
                    user_id=self._user_id
                )
            except TypeError:
                try:
                    self._callback_handler = CallbackHandler(
                        user_id=self._user_id
                    )
                except TypeError:
                    self._callback_handler = CallbackHandler()
        
        logger.info(f"Langfuse session updated - Session ID: {self._session_id}, User ID: {self._user_id}")
    
    def is_enabled(self) -> bool:
        """Langfuse가 활성화되어 있는지 확인"""
        return config.langfuse.enabled and LANGFUSE_AVAILABLE
    
    def flush(self):
        """대기 중인 모든 추적 데이터 전송"""
        if self._langfuse:
            self._langfuse.flush()
    
    @property
    def session_id(self) -> Optional[str]:
        """현재 세션 ID 반환"""
        return self._session_id
    
    @session_id.setter
    def session_id(self, value: str):
        """세션 ID 설정"""
        self._session_id = value
    
    @property
    def user_id(self) -> Optional[str]:
        """현재 사용자 ID 반환"""
        return self._user_id
    
    @user_id.setter
    def user_id(self, value: str):
        """사용자 ID 설정"""
        self._user_id = value


# 전역 Langfuse 매니저 인스턴스
langfuse_manager = LangfuseManager()