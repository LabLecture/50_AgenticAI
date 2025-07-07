# Text2SQL Agent 기술 문서

## 개요

Text2SQL Agent는 자연어 질의를 SQL 쿼리로 변환하고 실행하여 한국 증권 시장 데이터를 조회하는 핵심 모듈입니다. LangGraph 프레임워크를 사용하여 구현되었습니다.

## 구조 (`src/agents/text_to_sql_agent.py`)

### 주요 클래스

#### TextToSqlAgent

복잡한 자연어 질의 처리를 위한 멀티 스텝 에이전트

**주요 속성:**
- `llm`: OpenAI GPT 모델 (gpt-4o-mini)
- `database`: PostgreSQL 데이터베이스 연결
- `vector_store`: Weaviate 벡터 스토어 (선택적)
- `langfuse_manager`: 추적 및 모니터링

### 워크플로우 그래프

LangGraph를 사용한 상태 기반 처리:

```
START → get_schema_from_vector_db → generate_sql_query_with_schema → check_sql_query
                                                                           ↓
                                          [SQL 에러 시] ← get_sample_query_from_vector_db
                                                                           ↓
                                                              generate_sql_query_with_sample
                                                                           ↓
                                                                   check_sql_query
                                                                           ↓
                                                                  execute_sql_query
                                                                           ↓
                                                                    generate_answer → END
```

### SQL 에러 자동 수정 워크플로우 (NEW)

```
SQL 실행 오류 발생
        ↓
LLM에게 에러 메시지 전달
        ↓
에러 분석 및 수정된 SQL 생성
        ↓
재시도 (최대 3회)
        ↓
성공 시 결과 반환
```

### 핵심 노드 함수

#### 1. get_schema_from_vector_db
- Weaviate에서 관련 테이블 스키마 검색
- 자연어 질의와 유사한 스키마 정보 추출
- 벡터 검색을 통한 관련성 높은 테이블 선택

#### 2. generate_sql_query_with_schema
- LLM을 사용한 SQL 쿼리 생성 (스키마 기반)
- 테이블 스키마 정보 활용
- 한국어 자연어 처리 최적화
- **에러 분석 기능**: 이전 SQL 오류가 있으면 에러 메시지를 프롬프트에 포함

#### 3. generate_sql_query_with_sample
- 샘플 쿼리를 참조한 SQL 생성
- 복잡한 쿼리 패턴 학습
- **에러 수정**: PostgreSQL 힌트 메시지 활용하여 컬럼명/테이블명 자동 수정

#### 4. check_sql_query
- 생성된 SQL 구문 검사
- PostgreSQL 구문 유효성 확인
- 실행 전 사전 검증

#### 5. execute_sql_query
- 실제 SQL 쿼리 실행
- 데이터베이스 연결 및 결과 반환
- 에러 발생 시 상세 오류 메시지 수집

#### 6. generate_answer
- SQL 실행 결과를 자연어로 변환
- 한국어 형식으로 답변 생성
- 에러 상황에서도 사용자 친화적 답변 제공

#### 7. get_sample_query_from_vector_db
- 벡터 스토어에서 유사 쿼리 검색
- 컨텍스트 기반 SQL 개선
- 에러 시 상태 보존

### SQL 추출 및 에러 처리 개선

#### _extract_sql_from_response 메서드
- 다양한 LLM 응답 형식 지원:
  - ```sql ... ``` (표준 마크다운)
  - `sql ... ` (백틱 하나)
  - ::sql ... (이상한 접두사)
  - assistant ... (ChatGPT 형식)
- 자동 접두사 제거 및 정리

#### 에러 분석 프롬프트 개선
```
Previous SQL execution failed with error:
{error_message}

Please analyze the error and correct the SQL query accordingly.
Pay special attention to hints in error messages (e.g., "Perhaps you meant to reference the column...").
```

### 상태 관리

```python
class TextToSqlState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_query: str
    table_info: str
    sql_query: str
    query_result: list
    error_message: Optional[str]
    complexity: str
    sample_queries: str
    retry_count: int
    final_query: str
    execution_time: float
```

## 주요 기능

### 1. 자연어 처리

**지원하는 질의 유형:**
- 주식 가격 조회: "삼성전자 주가를 알려주세요"
- 시장 분석: "코스피 상위 10개 종목"
- 시계열 분석: "최근 1주일 거래량이 많은 종목"
- 섹터 분석: "IT 업종 시가총액 순위"

**한국어 최적화:**
- 종목명 정규화 (삼성전자 → 005930)
- 업종 분류 매핑
- 한국 증권 시장 용어 처리

### 2. SQL 생성 및 검증

**지원하는 SQL 패턴:**
- SELECT 문 (복잡한 JOIN 포함)
- 집계 함수 (SUM, AVG, COUNT, MAX, MIN)
- 정렬 및 필터링 (ORDER BY, WHERE)
- 윈도우 함수 (ROW_NUMBER, RANK)

**검증 과정:**
1. SQL 문법 검사
2. 보안 검증 (SQL Injection 방지)
3. 실행 권한 확인
4. 결과 크기 제한

### 3. 오류 처리 및 재시도

**재시도 메커니즘:**
- `MAX_TEXT_TO_SQL_RETRIES` 설정 (.env에서 3으로 설정)
- 상태 보존을 통한 무한 루프 방지
- 단계별 오류 복구

**일반적인 오류 시나리오:**
1. SQL 문법 오류 → 자동 수정 시도
2. 테이블/컬럼 오류 → 스키마 재확인
3. 실행 오류 → 쿼리 단순화

### 4. 성능 최적화

**캐싱 전략:**
- 테이블 스키마 정보 캐싱
- 벡터 스토어 검색 결과 캐싱
- LLM 응답 캐싱 (동일 질의)

**실행 시간 추적:**
- 각 단계별 실행 시간 측정
- 전체 처리 시간 보고
- 병목 지점 식별

## 설정 및 최적화

### 환경 변수 (.env)

```env
# Text2SQL 설정
MAX_TEXT_TO_SQL_RETRIES=3
SQL_GENERATION_TEMPERATURE=0.1
VECTOR_STORE_OPTIONAL=true

# LLM 설정
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.1

# 데이터베이스
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=market_asset
```

### LangGraph 설정

```python
# 재귀 한계 설정 (GraphRecursionError 방지)
config = {"recursion_limit": 100}

# 컴파일 옵션
graph = graph_builder.compile(
    checkpointer=checkpointer,
    interrupt_before=[]
)
```

## API 인터페이스

### 동기 API

```python
def query(self, user_query: str, session_id: str = None, user_id: str = None) -> Dict[str, Any]:
    """
    동기 방식으로 Text2SQL 질의 처리
    
    Args:
        user_query: 사용자 자연어 질의
        session_id: 세션 ID (Langfuse 추적용)
        user_id: 사용자 ID (Langfuse 추적용)
    
    Returns:
        Dict containing:
        - final_query: 최종 실행된 SQL
        - query_result: 실행 결과
        - error_message: 오류 메시지 (있는 경우)
        - execution_time: 실행 시간
    """
```

### 비동기 API

```python
async def aquery(self, user_query: str, session_id: str = None, user_id: str = None) -> Dict[str, Any]:
    """비동기 방식으로 Text2SQL 질의 처리"""
```

## 통합 구성요소

### Vector Store 연동

```python
if self.vector_store and self.vector_store.is_available():
    sample_queries = self.vector_store.search_similar_queries(
        query=user_query,
        limit=3
    )
```

### Langfuse 추적

```python
if self.langfuse_manager.is_enabled():
    trace = self.langfuse_manager.trace(
        name="text2sql_query",
        input={"user_query": user_query},
        session_id=session_id,
        user_id=user_id
    )
```

### 데이터베이스 연동

```python
# 비동기 PostgreSQL 연결
async with self.database.get_async_connection() as conn:
    result = await conn.fetch(sql_query)
```

## 모니터링 및 디버깅

### 로깅

```python
import logging
logger = logging.getLogger(__name__)

# 주요 이벤트 로깅
logger.info(f"Processing query: {user_query}")
logger.debug(f"Generated SQL: {sql_query}")
logger.error(f"Execution failed: {error}")
```

### 메트릭

- 질의 처리 시간
- 성공/실패율
- 재시도 횟수
- SQL 복잡도 분포

## 알려진 이슈 및 해결방법

### 1. GraphRecursionError

**문제:** LangGraph 재귀 한계 (25회) 초과

**해결:** recursion_limit을 100으로 증가

```python
config = {"recursion_limit": 100}
```

### 2. 상태 보존 문제

**문제:** 오류 발생 시 retry_count 초기화

**해결:** 상태 보존 로직 수정

```python
return {
    **state,  # 기존 상태 보존
    "messages": [AIMessage(content=f"Warning: {e}")],
    "error_message": None
}
```

### 3. SQL 파싱 오류

**문제:** LLM 응답에서 SQL 추출 실패

**해결:** 강화된 정규식 패턴

```python
def _extract_sql_from_response(self, response: str) -> str:
    patterns = [
        r"```sql\s*(.*?)\s*```",
        r"```\s*(SELECT.*?);?\s*```",
        r"Query:\s*(SELECT.*?)(?:\n|$)"
    ]
```

## 향후 개선 계획

1. **쿼리 캐싱**: Redis를 활용한 결과 캐싱
2. **배치 처리**: 여러 질의 동시 처리
3. **실시간 스트리밍**: 중간 결과 실시간 전송
4. **자동 최적화**: SQL 실행 계획 분석
5. **다국어 지원**: 영어 질의 처리 확장