# Langfuse 통합 기술 문서

## 개요

Langfuse는 LLM 애플리케이션의 추적, 모니터링, 디버깅을 위한 오픈소스 플랫폼입니다. M-Asset POC에서는 Text2SQL 에이전트의 성능 분석과 사용자 세션 추적을 위해 활용됩니다.

## 구조 (`src/core/langfuse_manager.py`)

### 주요 클래스

#### LangfuseManager

Langfuse 클라이언트 관리 및 추적 기능을 제공하는 싱글톤 클래스

**주요 속성:**
- `_client`: Langfuse 클라이언트 인스턴스
- `_session_id`: 현재 세션 ID
- `_user_id`: 현재 사용자 ID
- `_current_trace`: 현재 실행 중인 추적

### 핵심 기능

#### 1. 초기화 및 연결

```python
def __init__(self):
    """Langfuse 클라이언트 초기화"""
    self._client = None
    self._session_id = None
    self._user_id = None
    self._current_trace = None
    
    if config.langfuse.enabled and LANGFUSE_AVAILABLE:
        try:
            self._client = Langfuse(
                secret_key=config.langfuse.secret_key,
                public_key=config.langfuse.public_key,
                host=config.langfuse.host
            )
            logger.info("Langfuse client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Langfuse: {e}")
            self._client = None
```

#### 2. 추적 생성 및 관리

**추적 시작:**
```python
def trace(self, name: str, input: dict = None, session_id: str = None, user_id: str = None):
    """새로운 추적 시작"""
    if not self.is_enabled():
        return None
    
    try:
        # 세션 정보 업데이트
        if session_id:
            self._session_id = session_id
        if user_id:
            self._user_id = user_id
        
        # 추적 생성
        self._current_trace = self._client.trace(
            name=name,
            input=input,
            session_id=self._session_id,
            user_id=self._user_id,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "source": "m_asset_poc"
            }
        )
        
        logger.debug(f"Started trace: {name}")
        return self._current_trace
        
    except Exception as e:
        logger.error(f"Error creating trace: {e}")
        return None
```

**추적 종료:**
```python
def end_trace(self, output: dict = None, error: str = None):
    """현재 추적 종료"""
    if not self.is_enabled() or not self._current_trace:
        return
    
    try:
        self._current_trace.update(
            output=output,
            end_time=datetime.now(),
            metadata={
                "success": error is None,
                "error": error
            }
        )
        
        logger.debug("Trace ended successfully")
        self._current_trace = None
        
    except Exception as e:
        logger.error(f"Error ending trace: {e}")
```

#### 3. 스팬 관리

**스팬 생성:**
```python
def span(self, name: str, input: dict = None, span_type: str = "DEFAULT"):
    """현재 추적에 스팬 추가"""
    if not self.is_enabled() or not self._current_trace:
        return None
    
    try:
        span = self._current_trace.span(
            name=name,
            input=input,
            start_time=datetime.now(),
            metadata={
                "type": span_type,
                "session_id": self._session_id
            }
        )
        
        logger.debug(f"Created span: {name}")
        return span
        
    except Exception as e:
        logger.error(f"Error creating span: {e}")
        return None
```

#### 4. 이벤트 로깅

```python
def event(self, name: str, input: dict = None, output: dict = None, level: str = "DEFAULT"):
    """이벤트 로깅"""
    if not self.is_enabled():
        return None
    
    try:
        event = self._client.event(
            name=name,
            input=input,
            output=output,
            level=level,
            session_id=self._session_id,
            user_id=self._user_id,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "source": "m_asset_poc"
            }
        )
        
        logger.debug(f"Logged event: {name}")
        return event
        
    except Exception as e:
        logger.error(f"Error logging event: {e}")
        return None
```

#### 5. 세션 및 사용자 관리

```python
@property
def session_id(self) -> str:
    """현재 세션 ID 반환"""
    return self._session_id

@session_id.setter
def session_id(self, value: str):
    """세션 ID 설정"""
    self._session_id = value

@property
def user_id(self) -> str:
    """현재 사용자 ID 반환"""
    return self._user_id

@user_id.setter
def user_id(self, value: str):
    """사용자 ID 설정"""
    self._user_id = value
```

## 설정 및 환경

### 환경 변수 (.env)

```env
# Langfuse 설정
LANGFUSE_ENABLED=true
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx

# 또는 로컬 인스턴스
LANGFUSE_HOST=http://localhost:3000
```

### 설정 클래스 (`src/core/config.py`)

```python
@dataclass
class LangfuseConfig:
    enabled: bool = True
    host: str = "https://cloud.langfuse.com"
    public_key: str = ""
    secret_key: str = ""
    
    def __post_init__(self):
        if self.enabled and (not self.public_key or not self.secret_key):
            logger.warning("Langfuse keys not provided, disabling Langfuse")
            self.enabled = False
```

## Text2SQL Agent 통합

### 1. 추적 시작

```python
# Text2SQL 쿼리 처리 시작
def query(self, user_query: str, session_id: str = None, user_id: str = None):
    # Langfuse 추적 시작
    if langfuse_manager.is_enabled():
        langfuse_manager.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        langfuse_manager.user_id = user_id or "anonymous"
        
        trace = langfuse_manager.trace(
            name="text2sql_query",
            input={
                "user_query": user_query,
                "timestamp": datetime.now().isoformat()
            },
            session_id=langfuse_manager.session_id,
            user_id=langfuse_manager.user_id
        )
```

### 2. 단계별 스팬 추가

```python
# SQL 생성 단계
def generate_sql(state: TextToSqlState):
    span = None
    if langfuse_manager.is_enabled():
        span = langfuse_manager.span(
            name="sql_generation",
            input={
                "user_query": state["user_query"],
                "table_info": state["table_info"]
            },
            span_type="LLM"
        )
    
    try:
        # SQL 생성 로직
        result = llm.invoke(messages)
        
        # 성공 시 스팬 업데이트
        if span:
            span.update(
                output={"generated_sql": result.content},
                end_time=datetime.now()
            )
        
        return result
        
    except Exception as e:
        # 오류 시 스팬 업데이트
        if span:
            span.update(
                output={"error": str(e)},
                end_time=datetime.now(),
                level="ERROR"
            )
        raise
```

### 3. 벡터 검색 추적

```python
def get_sample_query_from_vector_db(state: TextToSqlState):
    """벡터 DB 검색 단계 추적"""
    span = None
    if langfuse_manager.is_enabled():
        span = langfuse_manager.span(
            name="vector_search",
            input={"query": state["user_query"]},
            span_type="RETRIEVAL"
        )
    
    try:
        # 벡터 검색 수행
        similar_queries = vector_store.search_similar_queries(
            query=state["user_query"],
            limit=3
        )
        
        # 검색 결과 추적
        if span:
            span.update(
                output={
                    "found_samples": len(similar_queries),
                    "samples": [
                        {
                            "query": sq["query"],
                            "certainty": sq["certainty"]
                        } for sq in similar_queries
                    ]
                },
                end_time=datetime.now()
            )
        
        return {
            **state,
            "sample_queries": format_sample_queries(similar_queries)
        }
        
    except Exception as e:
        if span:
            span.update(
                output={"error": str(e)},
                end_time=datetime.now(),
                level="ERROR"
            )
        
        logger.error(f"Vector DB query failed: {e}")
        return {
            **state,
            "sample_queries": ""
        }
```

### 4. 최종 결과 추적

```python
def finalize_query_processing(result: dict, error: str = None):
    """쿼리 처리 완료 시 추적 종료"""
    if langfuse_manager.is_enabled():
        # 성공/실패 이벤트 로깅
        langfuse_manager.event(
            name="query_completed",
            input={"has_error": error is not None},
            output={
                "final_query": result.get("final_query", ""),
                "result_count": len(result.get("query_result", [])),
                "execution_time": result.get("execution_time", 0),
                "error": error
            },
            level="ERROR" if error else "DEFAULT"
        )
        
        # 추적 종료
        langfuse_manager.end_trace(
            output={
                "success": error is None,
                "result": result,
                "total_execution_time": result.get("execution_time", 0)
            },
            error=error
        )
```

## A2A 서버 통합

### 1. A2A 메시지 추적

```python
async def on_message_send(self, params: MessageSendParams, context: ServerCallContext):
    """A2A 메시지 처리 추적"""
    # 세션 정보 설정
    session_id = f"a2a_session_{params.message.messageId}"
    user_id = "a2a_user"
    
    # Langfuse 추적 시작
    if langfuse_manager.is_enabled():
        langfuse_manager.session_id = session_id
        langfuse_manager.user_id = user_id
        
        trace = langfuse_manager.trace(
            name="a2a_message_processing",
            input={
                "message_id": params.message.messageId,
                "role": params.message.role,
                "content_length": len(str(params.message.parts))
            },
            session_id=session_id,
            user_id=user_id
        )
    
    try:
        # Text2SQL 서비스 호출
        result = await self._execute_text2sql_query(content, session_id, user_id)
        
        # 성공 추적
        if langfuse_manager.is_enabled():
            langfuse_manager.end_trace(
                output={
                    "response_message_id": f"response_{params.message.messageId}",
                    "sql_executed": result.get("final_query", ""),
                    "result_count": len(result.get("query_result", []))
                }
            )
        
        return response_message
        
    except Exception as e:
        # 오류 추적
        if langfuse_manager.is_enabled():
            langfuse_manager.end_trace(
                error=str(e)
            )
        
        return error_message
```

### 2. 스트리밍 추적

```python
async def on_message_send_stream(self, params: MessageSendParams, context: ServerCallContext):
    """A2A 스트리밍 메시지 추적"""
    session_id = f"a2a_stream_session_{params.message.messageId}"
    
    # 스트리밍 추적 시작
    if langfuse_manager.is_enabled():
        langfuse_manager.session_id = session_id
        langfuse_manager.user_id = "a2a_stream_user"
        
        trace = langfuse_manager.trace(
            name="a2a_streaming_processing",
            input={"message_id": params.message.messageId},
            session_id=session_id,
            user_id="a2a_stream_user"
        )
    
    # 각 스트리밍 단계별 이벤트 로깅
    if langfuse_manager.is_enabled():
        langfuse_manager.event(
            name="streaming_step",
            input={"step": "start"},
            output={"message": "질의를 처리하고 있습니다"}
        )
    
    yield start_message
    
    # ... 중간 단계들 ...
    
    if langfuse_manager.is_enabled():
        langfuse_manager.event(
            name="streaming_step",
            input={"step": "complete"},
            output={"message": "처리 완료"}
        )
        
        langfuse_manager.end_trace(
            output={"streaming_messages_sent": 5}
        )
    
    yield completion_message
```

## 대시보드 활용

### 1. 세션 분석

Langfuse 대시보드에서 확인할 수 있는 정보:

- **세션별 쿼리 수**: 사용자별 활동 패턴
- **평균 처리 시간**: 성능 모니터링
- **오류율**: 시스템 안정성 추적
- **인기 쿼리**: 사용 패턴 분석

### 2. 성능 메트릭

```python
# 커스텀 메트릭 추가
def log_performance_metrics(execution_time: float, query_complexity: str):
    """성능 메트릭 로깅"""
    if langfuse_manager.is_enabled():
        langfuse_manager.event(
            name="performance_metric",
            input={
                "metric_type": "execution_time",
                "query_complexity": query_complexity
            },
            output={
                "execution_time_ms": execution_time * 1000,
                "performance_category": "fast" if execution_time < 5.0 else "slow"
            }
        )
```

### 3. 오류 분석

```python
def log_error_details(error: Exception, context: dict):
    """상세 오류 정보 로깅"""
    if langfuse_manager.is_enabled():
        langfuse_manager.event(
            name="error_analysis",
            input=context,
            output={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "stack_trace": traceback.format_exc()
            },
            level="ERROR"
        )
```

## 모니터링 및 알림

### 1. 품질 메트릭

```python
def track_query_quality(user_query: str, sql_result: list, execution_time: float):
    """쿼리 품질 추적"""
    if langfuse_manager.is_enabled():
        quality_score = calculate_quality_score(user_query, sql_result, execution_time)
        
        langfuse_manager.event(
            name="query_quality",
            input={"user_query": user_query},
            output={
                "quality_score": quality_score,
                "result_count": len(sql_result),
                "execution_time": execution_time,
                "quality_category": "high" if quality_score > 0.8 else "medium" if quality_score > 0.5 else "low"
            }
        )
```

### 2. 사용자 피드백 연동

```python
def log_user_feedback(query_id: str, feedback: dict):
    """사용자 피드백 로깅"""
    if langfuse_manager.is_enabled():
        langfuse_manager.event(
            name="user_feedback",
            input={"query_id": query_id},
            output={
                "satisfaction": feedback.get("satisfaction"),
                "accuracy": feedback.get("accuracy"),
                "usefulness": feedback.get("usefulness"),
                "comments": feedback.get("comments", "")
            }
        )
```

## 알려진 제한사항

1. **네트워크 의존성**: Langfuse 서버 연결 필요
2. **성능 오버헤드**: 추적 데이터 전송으로 인한 지연
3. **데이터 민감성**: 쿼리 내용이 외부 서버로 전송
4. **저장소 제한**: 무료 플랜의 데이터 보존 기간 제한

## 향후 개선 계획

1. **로컬 캐싱**: 오프라인 시 데이터 로컬 저장
2. **배치 전송**: 성능 향상을 위한 배치 처리
3. **데이터 마스킹**: 민감 정보 자동 마스킹
4. **커스텀 메트릭**: 비즈니스 특화 지표 추가
5. **실시간 알림**: 임계값 기반 알림 시스템