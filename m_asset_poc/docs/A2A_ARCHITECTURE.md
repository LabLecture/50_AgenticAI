# A2A (Agent-to-Agent) 아키텍처 문서

## 개요

M-Asset POC 프로젝트에서 A2A (Agent-to-Agent) 프로토콜을 구현하여 Text2SQL 에이전트를 외부 시스템과 연동할 수 있도록 합니다.

## 구성 요소

### 1. A2A Text2SQL Agent (`src/a2a/text2sql_agent.py`)

#### 주요 클래스

- **Text2SQLRequestHandler**: A2A 요청 처리 핸들러
- **Text2SQLAgent**: A2A 프로토콜을 사용하는 Text2SQL 에이전트

#### 지원 메서드

1. **message/send** (동기 처리)
   - 단일 메시지를 받아 즉시 응답 반환
   - JSON 형태의 SQL 실행 결과 제공

2. **message/stream** (스트리밍 처리)
   - 실시간 처리 상태를 스트리밍으로 전달
   - 단계별 진행 상황 알림 (SQL 생성 → 실행 → 결과 정리)

3. **tasks/get, tasks/cancel** (작업 관리)
   - 장기 실행 작업 조회 및 취소 (현재 미구현)

### 2. A2A 설정 (`src/a2a/config.py`)

```python
@dataclass
class A2AConfig:
    agent_name: str = "M-Asset Text2SQL Agent"
    agent_description: str = "한국 증권 시장 데이터에 대한 자연어 질의를 SQL로 변환하고 실행"
    agent_version: str = "1.0.0"
    streaming_enabled: bool = True
    push_notifications_enabled: bool = False
```

### 3. 메시지 파싱

A2A 표준 메시지 형식을 파싱하여 텍스트 내용 추출:

```python
# 메시지 구조: Message.parts[].kind == 'text'
for part in params.message.parts:
    actual_part = part.root if hasattr(part, 'root') else part
    if hasattr(actual_part, 'kind') and actual_part.kind == 'text':
        content += str(actual_part.text) + " "
```

## 서버 구성

### FastAPI 애플리케이션

- **포트**: 8011
- **엔드포인트**: `/` (JSON-RPC)
- **Well-known**: `/.well-known/agent.json` (에이전트 카드)
- **문서**: `/docs` (OpenAPI/Swagger)

### Agent Card

```json
{
  "name": "M-Asset Text2SQL Agent",
  "description": "한국 증권 시장 데이터에 대한 자연어 질의를 SQL로 변환하고 실행",
  "version": "1.0.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": false,
    "stateTransitionHistory": true
  },
  "skills": [
    {
      "id": "text2sql",
      "name": "Text-to-SQL 질의 처리",
      "description": "자연어 질의를 SQL로 변환하고 실행하여 결과를 반환합니다",
      "tags": ["database", "sql", "nlp", "korean", "financial-data"]
    }
  ]
}
```

## 요청/응답 예시

### 동기 요청 (message/send)

**요청:**
```json
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "test_123",
      "role": "user",
      "parts": [
        {
          "kind": "text",
          "text": "삼성전자의 주가를 알려주세요"
        }
      ]
    }
  },
  "id": 1
}
```

**응답:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "messageId": "response_test_123",
    "role": "agent",
    "parts": [
      {
        "text": "{\"query\": \"삼성전자의 주가를 알려주세요\", \"sql\": \"SELECT * FROM stock_prices WHERE symbol = '005930'\", \"result\": [...]}"
      }
    ],
    "createdAt": "2025-06-27T10:30:00Z"
  },
  "id": 1
}
```

### 스트리밍 요청 (message/stream)

**요청:** 동일한 형식

**응답:** Server-Sent Events (SSE) 형태로 여러 메시지 스트리밍
```
data: {"messageId": "stream_start_test_123", "role": "agent", "parts": [{"text": "질의를 처리하고 있습니다..."}]}

data: {"messageId": "stream_sql_test_123", "role": "agent", "parts": [{"text": "SQL 쿼리를 생성하고 있습니다..."}]}

data: {"messageId": "stream_final_test_123", "role": "agent", "parts": [{"text": "{\"query\": \"...\", \"result\": [...]}"}]}
```

## 오류 처리

### 일반적인 오류 시나리오

1. **메시지 파싱 실패**: 하드코딩된 기본 쿼리 사용
2. **SQL 생성 오류**: 오류 메시지와 함께 빈 결과 반환
3. **데이터베이스 연결 실패**: 에러 상태 메시지 반환

### 로깅

- 모든 요청/응답을 INFO 레벨로 로깅
- 오류는 ERROR 레벨로 상세 로깅
- 로그는 `logs/a2a_server_YYYYMMDD_HHMMSS.log`에 저장

## 통합 구성

### Text2SQL 서비스 연동

```python
result = self.text_to_sql_service.query(
    user_query=content,
    session_id=session_id,
    user_id=user_id
)
```

### Langfuse 추적 통합

```python
if langfuse_manager.is_enabled():
    langfuse_manager.session_id = session_id
    langfuse_manager.user_id = user_id
```

## 실행 방법

### 1. 서버 시작

```bash
# 가상환경 활성화
source venv/bin/activate

# A2A 서버 시작
python start_a2a_server.py
```

### 2. 테스트

```bash
# Agent Card 확인
curl http://localhost:8011/.well-known/agent.json

# 메시지 전송 테스트
curl -X POST http://localhost:8011/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "test_123",
        "role": "user",
        "parts": [{"kind": "text", "text": "삼성전자 주가"}]
      }
    },
    "id": 1
  }'
```

## 알려진 제한사항

1. **메시지 파싱**: 복잡한 Part 구조 처리 시 일부 제한
2. **작업 관리**: tasks/* 메서드들은 기본 구조만 구현
3. **인증**: 현재 인증 메커니즘 미구현
4. **푸시 알림**: 현재 비활성화 상태

## 향후 개선 계획

1. 작업 관리 메서드 완전 구현
2. 인증 및 권한 관리 추가
3. 메시지 파싱 로버스트성 향상
4. 성능 모니터링 및 메트릭 추가