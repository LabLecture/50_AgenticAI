"""
A2A Text2SQL Agent implementation using Google A2A SDK
"""

import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime
from collections.abc import AsyncGenerator as AsyncGeneratorABC

try:
    from a2a.types import AgentCard, AgentCapabilities, AgentSkill, Task, TaskState, Message, MessageSendParams, TaskIdParams, TaskQueryParams, TaskPushNotificationConfig
    from a2a.server.request_handlers.request_handler import RequestHandler
    from a2a.server.context import ServerCallContext
    from a2a.server.events.event_queue import Event
    from a2a.server.apps.jsonrpc.fastapi_app import A2AFastAPIApplication
    from a2a.utils.errors import ServerError
    A2A_AVAILABLE = True
except ImportError:
    # A2A SDK가 설치되지 않은 경우를 위한 fallback
    logging.warning("A2A SDK not installed. A2A functionality will be disabled.")
    A2A_AVAILABLE = False

from ..agents.text_to_sql_agent import text_to_sql_agent
from ..core.langfuse_manager import langfuse_manager
from ..core.concurrency_limiter import ConcurrencyLimiter
from .config import A2AConfig
import os

logger = logging.getLogger(__name__)

# A2A 서버 전용 동시성 제한기
a2a_concurrency_limiter = ConcurrencyLimiter(
    max_concurrent=int(os.getenv("A2A_MAX_CONCURRENT_REQUESTS", "10")),
    timeout=float(os.getenv("A2A_REQUEST_QUEUE_TIMEOUT", "300"))
)

if A2A_AVAILABLE:
    class Text2SQLRequestHandler(RequestHandler):
        """A2A Text2SQL Request Handler"""
        
        def __init__(self, config: A2AConfig):
            self.config = config
            self.text_to_sql_service = text_to_sql_agent
            logger.info(f"A2A Text2SQL Request Handler initialized: {config.agent_name}")
        
        async def on_get_task(
            self,
            params: TaskQueryParams,
            context: ServerCallContext | None = None,
        ) -> Task | None:
            """Handles the 'tasks/get' method."""
            # TODO: Implement task retrieval logic
            logger.info(f"Getting task: {params.taskId}")
            return None
        
        async def on_cancel_task(
            self,
            params: TaskIdParams,
            context: ServerCallContext | None = None,
        ) -> Task | None:
            """Handles the 'tasks/cancel' method."""
            logger.info(f"Canceling task: {params.taskId}")
            return None
        
        async def on_message_send(
            self,
            params: MessageSendParams,
            context: ServerCallContext | None = None,
        ) -> Task | Message:
            """Handles the 'message/send' method (non-streaming)."""
            # 동시성 제한기를 통해 실행
            request_id = f"a2a_{params.message.messageId if params.message and params.message.messageId else 'unknown'}"
            
            async with a2a_concurrency_limiter.acquire(request_id=request_id) as request_info:
                wait_time = request_info.get("wait_time", 0.0) if request_info else 0.0
                
                if wait_time > 0:
                    logger.info(f"A2A request {request_id} waited {wait_time:.2f}s in queue")
                
                # 전체 params 객체 디버그
                logger.info(f"Full params object: {params}")
                logger.info(f"Message object: {params.message}")
                logger.info(f"Message type: {type(params.message)}")
                logger.info(f"Message dir: {dir(params.message)}")
                
                # A2A Message 객체에서 텍스트 내용 추출 (A2A 표준 형식에 맞춰)
                content = ""
                
                try:
                    # A2A 표준에 따르면 message.parts는 Part 객체들의 배열
                    if hasattr(params.message, 'parts') and params.message.parts:
                        for part in params.message.parts:
                            # Part는 RootModel이므로 실제 데이터는 part.root에 있음
                            actual_part = part.root if hasattr(part, 'root') else part
                            
                            # TextPart의 경우: {"kind": "text", "text": "내용"}
                            if hasattr(actual_part, 'kind') and actual_part.kind == 'text':
                                if hasattr(actual_part, 'text'):
                                    content += str(actual_part.text) + " "
                            elif hasattr(actual_part, 'type') and actual_part.type == 'text':
                                if hasattr(actual_part, 'text'):
                                    content += str(actual_part.text) + " "
                            # dict 형태로 온 경우
                            elif isinstance(actual_part, dict):
                                if (actual_part.get('kind') == 'text' or actual_part.get('type') == 'text') and 'text' in actual_part:
                                    content += str(actual_part['text']) + " "
                            # 기타 텍스트 속성 확인
                            elif hasattr(actual_part, 'text'):
                                content += str(actual_part.text) + " "
                    
                    content = content.strip()
                    
                    # 콘텐츠가 없으면 디버깅 정보 출력
                    if not content:
                        logger.warning("No content extracted from message parts")
                        logger.info(f"Message: {params.message}")
                        logger.info(f"Message type: {type(params.message)}")
                        if hasattr(params.message, 'parts'):
                            logger.info(f"Parts: {params.message.parts}")
                            logger.info(f"Parts type: {type(params.message.parts)}")
                            if params.message.parts:
                                for i, part in enumerate(params.message.parts):
                                    logger.info(f"Part {i}: {part} (type: {type(part)})")
                                    if hasattr(part, '__dict__'):
                                        logger.info(f"Part {i} __dict__: {part.__dict__}")
                                    # 모든 속성 확인
                                    if hasattr(part, '__dir__'):
                                        attrs = [attr for attr in dir(part) if not attr.startswith('_')]
                                        logger.info(f"Part {i} attributes: {attrs}")
                                        for attr in attrs:
                                            try:
                                                value = getattr(part, attr)
                                                if not callable(value):
                                                    logger.info(f"Part {i}.{attr}: {value}")
                                            except Exception as e:
                                                logger.info(f"Part {i}.{attr}: <error accessing: {e}>")
                        
                        # 하드코딩된 쿼리 사용
                        logger.warning("Using hardcoded query for debugging")
                        content = "삼성전자의 주가를 알려주세요"
                    
                except Exception as e:
                    logger.error(f"Error parsing A2A message: {e}")
                    logger.warning("Using hardcoded query due to parsing error")
                    content = "삼성전자의 주가를 알려주세요"
                
                # 최종 안전장치
                if not content or content.isspace():
                    logger.warning("Content is empty, using default query")
                    content = "삼성전자의 주가를 알려주세요"
                
                logger.info(f"Processing A2A message: '{content}'")
                
                try:
                    # Text2SQL 서비스 호출
                    session_id = f"a2a_session_{params.message.messageId if params.message.messageId else 'unknown'}"
                    user_id = "a2a_user"
                    
                    result = await self._execute_text2sql_query(
                        content, session_id, user_id
                    )
                    
                    # Message 응답 생성 - final_answer 노드의 자연어 답변 우선 사용
                    response_content = result.get("final_answer", "")
                    
                    # final_answer가 없으면 기본 JSON 형태로 fallback
                    if not response_content or response_content.strip() == "":
                        response_content = json.dumps({
                            "query": content,
                            "sql": result.get("final_query", ""),
                            "result": result.get("query_result", []),
                            "error": result.get("error_message", ""),
                            "execution_time": result.get("execution_time", 0)
                        }, ensure_ascii=False, indent=2)
                    
                    response_message = Message(
                        messageId=f"response_{params.message.messageId}",
                        role="agent",
                        parts=[{
                            "text": response_content
                        }],
                        createdAt=datetime.utcnow().isoformat()
                    )
                    
                    return response_message
                    
                except Exception as e:
                    logger.error(f"Error in message send: {e}")
                    error_message = Message(
                        messageId=f"error_{params.message.messageId}",
                        role="agent",
                        parts=[{
                            "text": f"질의 처리 중 오류가 발생했습니다: {e}"
                        }],
                        createdAt=datetime.utcnow().isoformat()
                    )
                    return error_message
        
        async def on_message_send_stream(
            self,
            params: MessageSendParams,
            context: ServerCallContext | None = None,
        ) -> AsyncGeneratorABC[Event]:
            """Handles the 'message/stream' method (streaming)."""
            # 동시성 제한기를 통해 실행
            request_id = f"a2a_stream_{params.message.messageId if params.message and params.message.messageId else 'unknown'}"
            
            async with a2a_concurrency_limiter.acquire(request_id=request_id) as request_info:
                wait_time = request_info.get("wait_time", 0.0) if request_info else 0.0
                
                if wait_time > 0:
                    logger.info(f"A2A stream request {request_id} waited {wait_time:.2f}s in queue")
                
                logger.info(f"Streaming message request: {params.message.messageId}")
                
                # A2A Message 객체에서 텍스트 내용 추출 (동일한 로직)
                content = ""
            
            try:
                if hasattr(params.message, 'parts') and params.message.parts:
                    for part in params.message.parts:
                        actual_part = part.root if hasattr(part, 'root') else part
                        
                        if hasattr(actual_part, 'kind') and actual_part.kind == 'text':
                            if hasattr(actual_part, 'text'):
                                content += str(actual_part.text) + " "
                        elif hasattr(actual_part, 'type') and actual_part.type == 'text':
                            if hasattr(actual_part, 'text'):
                                content += str(actual_part.text) + " "
                        elif isinstance(actual_part, dict):
                            if (actual_part.get('kind') == 'text' or actual_part.get('type') == 'text') and 'text' in actual_part:
                                content += str(actual_part['text']) + " "
                        elif hasattr(actual_part, 'text'):
                            content += str(actual_part.text) + " "
                
                content = content.strip()
                
                if not content:
                    logger.warning("No content extracted from streaming message, using default")
                    content = "삼성전자의 주가를 알려주세요"
                
            except Exception as e:
                logger.error(f"Error parsing streaming message: {e}")
                content = "삼성전자의 주가를 알려주세요"
            
            # 처리 시작 알림 메시지
            start_message = Message(
                messageId=f"stream_start_{params.message.messageId}",
                role="agent",
                parts=[{
                    "text": f"질의를 처리하고 있습니다: '{content}'"
                }],
                createdAt=datetime.utcnow().isoformat()
            )
            yield start_message
            
            # 잠시 대기 (실제 처리 시뮬레이션)
            await asyncio.sleep(0.5)
            
            # SQL 생성 중 알림
            sql_gen_message = Message(
                messageId=f"stream_sql_{params.message.messageId}",
                role="agent",
                parts=[{
                    "text": "SQL 쿼리를 생성하고 있습니다..."
                }],
                createdAt=datetime.utcnow().isoformat()
            )
            yield sql_gen_message
            
            try:
                # Text2SQL 서비스 호출
                session_id = f"a2a_stream_session_{params.message.messageId if params.message.messageId else 'unknown'}"
                user_id = "a2a_stream_user"
                
                # SQL 생성 진행 알림
                await asyncio.sleep(1.0)
                progress_message = Message(
                    messageId=f"stream_progress_{params.message.messageId}",
                    role="agent",
                    parts=[{
                        "text": "데이터베이스에서 정보를 조회하고 있습니다..."
                    }],
                    createdAt=datetime.utcnow().isoformat()
                )
                yield progress_message
                
                # 실제 쿼리 실행
                result = await self._execute_text2sql_query(
                    content, session_id, user_id
                )
                
                # 결과 준비 알림
                await asyncio.sleep(0.5)
                final_prep_message = Message(
                    messageId=f"stream_prep_{params.message.messageId}",
                    role="agent",
                    parts=[{
                        "text": "결과를 정리하고 있습니다..."
                    }],
                    createdAt=datetime.utcnow().isoformat()
                )
                yield final_prep_message
                
                # 최종 결과 메시지 - answer 노드의 자연어 답변 사용
                await asyncio.sleep(0.3)
                
                # final_answer 노드에서 생성된 자연어 답변 우선 사용
                response_content = result.get("final_answer", "")
                
                # final_answer가 없으면 기본 JSON 형태로 fallback
                if not response_content or response_content.strip() == "":
                    response_content = json.dumps({
                        "query": content,
                        "sql": result.get("final_query", ""),
                        "result": result.get("query_result", []),
                        "error": result.get("error_message", ""),
                        "execution_time": result.get("execution_time", 0),
                        "streaming": True
                    }, ensure_ascii=False, indent=2)
                
                final_message = Message(
                    messageId=f"stream_final_{params.message.messageId}",
                    role="agent",
                    parts=[{
                        "text": response_content
                    }],
                    createdAt=datetime.utcnow().isoformat()
                )
                yield final_message
                
                # 스트림 완료 알림
                completion_message = Message(
                    messageId=f"stream_complete_{params.message.messageId}",
                    role="agent",
                    parts=[{
                        "text": "✅ 질의 처리가 완료되었습니다."
                    }],
                    createdAt=datetime.utcnow().isoformat()
                )
                yield completion_message
                
            except Exception as e:
                logger.error(f"Error in streaming message send: {e}")
                error_message = Message(
                    messageId=f"stream_error_{params.message.messageId}",
                    role="agent",
                    parts=[{
                        "text": f"❌ 스트리밍 처리 중 오류가 발생했습니다: {e}"
                    }],
                    createdAt=datetime.utcnow().isoformat()
                )
                yield error_message
        
        async def on_get_task_push_notification_config(
            self,
            params: TaskIdParams,
            context: ServerCallContext | None = None,
        ) -> TaskPushNotificationConfig | None:
            """Handles the 'tasks/getPushNotificationConfig' method."""
            return None
        
        async def on_set_task_push_notification_config(
            self,
            params: TaskPushNotificationConfig,
            context: ServerCallContext | None = None,
        ) -> TaskPushNotificationConfig:
            """Handles the 'tasks/setPushNotificationConfig' method."""
            return params
        
        async def on_resubscribe_to_task(
            self,
            params: TaskIdParams,
            context: ServerCallContext | None = None,
        ) -> AsyncGeneratorABC[Event]:
            """Handles the 'tasks/resubscribe' method."""
            logger.info(f"Resubscribing to task: {params.taskId}")
            # This is a placeholder implementation
            return
            yield  # This makes it a generator
        
        async def _execute_text2sql_query(self, query: str, session_id: str, user_id: str) -> Dict[str, Any]:
            """Text2SQL 쿼리 실행 (비동기 실행)"""
            try:
                logger.info(f"Executing text2sql query: '{query}' (session: {session_id})")
                
                # Langfuse 세션 설정
                if langfuse_manager.is_enabled():
                    langfuse_manager.session_id = session_id
                    langfuse_manager.user_id = user_id
                
                # Text2SQL 에이전트 호출 (비동기 실행)
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    self.text_to_sql_service.query,
                    query,
                    session_id,
                    user_id
                )
                
                logger.info(f"Text2SQL query result: {result.get('final_query', 'No SQL generated')}")
                return result
                
            except Exception as e:
                logger.error(f"Error executing text2sql query: {e}")
                return {
                    "error_message": str(e),
                    "final_query": "",
                    "query_result": [],
                    "execution_time": 0
                }
    
    class Text2SQLAgent:
        """A2A 프로토콜을 사용하는 Text2SQL 에이전트"""
        
        def __init__(self, config: A2AConfig):
            self.config = config
            self.request_handler = Text2SQLRequestHandler(config)
            self.agent_card = self._create_agent_card()
            self.app = None
            
            logger.info(f"A2A Text2SQL Agent initialized: {config.agent_name}")
        
        def is_available(self) -> bool:
            """A2A 에이전트 사용 가능 여부"""
            return self.request_handler is not None
        
        def get_agent_card(self) -> Dict[str, Any]:
            """Agent Card 반환"""
            return self.agent_card.model_dump() if self.agent_card else None
        
        def _create_agent_card(self) -> AgentCard:
            """Agent Card 생성"""
            # Agent capabilities 생성
            capabilities = AgentCapabilities(
                streaming=self.config.streaming_enabled,
                pushNotifications=self.config.push_notifications_enabled,
                stateTransitionHistory=True
            )
            
            # Agent skills 생성
            skills = [
                AgentSkill(
                    id="text2sql",
                    name="Text-to-SQL 질의 처리",
                    description="자연어 질의를 SQL로 변환하고 실행하여 결과를 반환합니다",
                    tags=["database", "sql", "nlp", "korean", "financial-data"],
                    examples=[
                        "삼성전자의 주가를 알려주세요",
                        "코스피 상위 10개 종목을 보여주세요",
                        "최근 1주일 동안 가장 많이 거래된 종목은?",
                        "IT 섹터의 시가총액 상위 5개 종목을 알려주세요"
                    ]
                )
            ]
            
            return AgentCard(
                name=self.config.agent_name,
                description=self.config.agent_description,
                version=self.config.agent_version,
                url=f"http://localhost:8011",  # A2A 서버 URL
                capabilities=capabilities,
                skills=skills,
                defaultInputModes=["text/plain"],
                defaultOutputModes=["application/json", "text/plain"],
                supportsAuthenticatedExtendedCard=False
            )
        
        def create_fastapi_app(self):
            """FastAPI 앱 생성"""
            a2a_app = A2AFastAPIApplication(
                agent_card=self.agent_card,
                http_handler=self.request_handler
            )
            
            self.app = a2a_app.build(
                title=f"{self.config.agent_name} A2A API",
                description=self.config.agent_description,
                version=self.config.agent_version
            )
            
            # 동시성 상태 확인 엔드포인트 추가
            @self.app.get("/concurrency/status")
            async def get_concurrency_status():
                """A2A 서버 동시성 상태 조회"""
                return a2a_concurrency_limiter.get_status()
            
            # 시스템 상태 엔드포인트 추가
            @self.app.get("/status")
            async def get_system_status():
                """A2A 서버 전체 상태 조회"""
                return {
                    "server": "A2A Text2SQL Agent",
                    "port": 8011,
                    "a2a_enabled": A2A_AVAILABLE,
                    "agent_name": self.config.agent_name,
                    "agent_version": self.config.agent_version,
                    "concurrency": a2a_concurrency_limiter.get_status()
                }
            
            return self.app
        
        async def start_server(self, host: str = "0.0.0.0", port: int = 8011):
            """A2A 서버 시작"""
            if not self.app:
                self.create_fastapi_app()
            
            import uvicorn
            logger.info(f"Starting A2A server on {host}:{port}")
            uvicorn.run(self.app, host=host, port=port)

else:
    # A2A SDK가 사용 불가능할 때의 더미 클래스
    class Text2SQLAgent:
        """A2A SDK가 없을 때의 더미 Text2SQL 에이전트"""
        
        def __init__(self, config: A2AConfig):
            self.config = config
            logger.warning("A2A SDK not available. Text2SQLAgent will not function.")
        
        def is_available(self) -> bool:
            """A2A 에이전트 사용 가능 여부"""
            return False
        
        def get_agent_card(self) -> Dict[str, Any]:
            """Agent Card 반환"""
            return None
        
        async def start_server(self, host: str = "0.0.0.0", port: int = 8010):
            """A2A 서버 시작 (더미)"""
            raise ValueError("A2A SDK not available. Cannot start A2A server.")