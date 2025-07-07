# M-Asset POC (증권 종목 에이전트)

증권 종목 관련 자연어 질의를 SQL로 변환하고 실행하는 마켓 에이전트 POC 프로젝트입니다.

## 프로젝트 구조

```
m_asset_poc/
├── src/                           # 소스 코드
│   ├── __init__.py
│   ├── a2a/                       # A2A (Agent-to-Agent) 서버
│   │   ├── __init__.py
│   │   ├── config.py              # A2A 설정
│   │   ├── standalone_server.py   # 독립 실행형 A2A 서버
│   │   └── text2sql_agent.py      # A2A Text2SQL 에이전트
│   ├── core/                      # 핵심 구성 요소
│   │   ├── __init__.py
│   │   ├── config.py              # 설정 관리
│   │   ├── database.py            # 데이터베이스 연결 (asyncpg)
│   │   ├── vector_store.py        # Weaviate 벡터 스토어 관리
│   │   ├── langfuse_manager.py    # Langfuse 추적 시스템
│   │   ├── concurrency_limiter.py # 동시성 제한 관리
│   │   ├── llm_cache_manager.py   # LLM 응답 캐싱 (Redis)
│   │   └── weaviate_pool.py       # Weaviate 연결 풀
│   ├── agents/                    # 에이전트 모듈
│   │   ├── __init__.py
│   │   └── text_to_sql_agent.py   # LangGraph 기반 Text-to-SQL 에이전트
│   ├── api/                       # API 서버
│   │   ├── __init__.py
│   │   └── server.py              # FastAPI 서버 (port 8010)
│   └── utils/                     # 유틸리티
│       ├── __init__.py
│       ├── logging_config.py      # 로깅 설정
│       ├── weaviate_setup.py      # Weaviate 초기 설정
│       └── default_schema.py      # 기본 스키마 정보 (fallback)
├── tests/                         # 테스트 코드
├── docs/                          # 기술 문서
│   ├── README.md                  # 기본 문서
│   ├── A2A_ARCHITECTURE.md        # A2A 아키텍처 문서
│   ├── TEXT2SQL_AGENT.md          # Text2SQL 에이전트 문서
│   ├── VECTOR_STORE.md            # 벡터 스토어 문서
│   └── LANGFUSE_INTEGRATION.md    # Langfuse 통합 문서
├── logs/                          # 로그 파일 저장소
├── main.py                        # 메인 엔트리 포인트
├── start_a2a_server.py            # A2A 서버 시작 스크립트
├── query_withexcel.py             # Excel 파일 배치 처리
├── requirements.txt               # 의존성 패키지
├── CLAUDE.md                      # 프로젝트 지침 및 개발 로그
├── Multi_Agent_v1.4.ipynb        # 원본 노트북 (참조용)
└── Weaviate_table_info_masset1.ipynb  # 원본 노트북 (참조용)
```

## 주요 기능

- **Text-to-SQL 변환**: 자연어 질의를 PostgreSQL 쿼리로 자동 변환
- **A2A 프로토콜**: Agent-to-Agent 통신 지원 (port 8011)
- **벡터 검색**: Weaviate를 이용한 스키마 및 샘플 쿼리 검색 (선택적)
- **LangGraph 에이전트**: 다단계 쿼리 생성 및 검증 워크플로
- **추적 시스템**: Langfuse를 통한 session_id, user_id 기반 추적 (선택적)
- **REST API**: FastAPI 기반 웹 서비스 (port 8010)
- **스트리밍 지원**: A2A 메시지 스트리밍 처리
- **Excel 배치 처리**: 여러 질의를 Excel 파일로 일괄 처리 및 결과 저장
- **동시성 제어**: 최대 10명 동시 접속 제한 및 대기열 관리
- **LLM 캐싱**: Redis 기반 SQL 생성 결과 캐싱 (TTL 설정 가능)
- **연결 풀링**: Weaviate 연결 풀을 통한 효율적인 연결 관리

## 설치 및 설정

> **💡 빠른 시작**: Docker를 사용하면 복잡한 환경 설정 없이 바로 시작할 수 있습니다. [Docker 배포](#docker-배포) 섹션을 참조하세요.

### 1. 로컬 환경 설치

#### 의존성 설치

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

#### 환경 변수 설정

`.env` 파일을 생성하거나 환경 변수를 설정하세요.
벡터 스토어 없이 실행하려면 `.env.example`을 참조하세요:

```bash
# 데이터베이스 설정
DB_USER=aitheuser1
DB_PASSWORD=aithepwd8#
DB_HOST=192.168.1.204
DB_PORT=55432
DB_NAME=skku

# Ollama 설정
OLLAMA_BASE_URL=http://192.168.1.203:11434
OLLAMA_EMBEDDING_MODEL=bge-m3:latest

# VLLM 설정
VLLM_SERVER_URL=http://192.168.1.239/vllm9/v1
VLLM_MODEL_NAME=qwencoder-32b
VLLM_API_KEY=EMPTY
VLLM_TEMPERATURE=0

# Weaviate 설정
WEAVIATE_HOST=192.168.1.203
WEAVIATE_PORT=8585
WEAVIATE_SCHEMA_COLLECTION=m_asset_hybrid_1
WEAVIATE_SAMPLE_COLLECTION=m_asset_sample_query_2_hint

# Langfuse 설정
LANGFUSE_PUBLIC_KEY=pk-lf-9432a302-838d-4480-8839-5a8ecdadf9b6
LANGFUSE_SECRET_KEY=sk-lf-58132035-a6ff-4848-9e96-1dda026f4a83
LANGFUSE_HOST=https://us.cloud.langfuse.com

# API 설정
API_HOST=0.0.0.0
API_PORT=8010
API_DEBUG=false

# 기타 설정
MAX_TEXT_TO_SQL_RETRIES=3

# 선택적 기능 설정
WEAVIATE_ENABLED=true      # false로 설정하면 벡터 스토어 없이 실행
LANGFUSE_ENABLED=true      # false로 설정하면 추적 시스템 없이 실행
VECTOR_STORE_OPTIONAL=true # 벡터 스토어 연결 실패 시에도 계속 실행

# 동시성 제어 설정
MAX_CONCURRENT_REQUESTS=10        # API 서버 최대 동시 요청 수
A2A_MAX_CONCURRENT_REQUESTS=10    # A2A 서버 최대 동시 요청 수
REQUEST_QUEUE_TIMEOUT=300         # 대기열 타임아웃 (초)

# LLM 캐싱 설정
LLM_CACHE_ENABLED=true            # LLM 응답 캐싱 활성화
LLM_CACHE_TTL=3600                # 캐시 TTL (초, 기본 1시간)
REDIS_HOST=localhost              # Redis 호스트
REDIS_PORT=6379                   # Redis 포트
REDIS_PASSWORD=                   # Redis 비밀번호 (선택사항)

# 벡터 스토어 연결 풀 설정
VECTOR_STORE_USE_POOL=true        # 연결 풀 사용 여부
VECTOR_STORE_MIN_CONNECTIONS=2    # 최소 연결 수
VECTOR_STORE_MAX_CONNECTIONS=10   # 최대 연결 수
```

**빠른 시작 (벡터 스토어 없이):**
```bash
# .env.example을 복사하여 사용
cp .env.example .env
```

### 2. Weaviate 벡터 스토어 설정

**기존 데이터가 있는 경우 (권장):**
- 기존 Weaviate 컬렉션을 그대로 사용합니다
- `WEAVIATE_ENABLED=true`로 설정하고 바로 서버 실행

**새로 설정하는 경우:**
```bash
python main.py --mode setup
```

**벡터 스토어 없이 실행하는 경우:**
- `WEAVIATE_ENABLED=false`로 설정

## 사용 방법

### 1. 서버 실행

#### 간편한 서버 관리 (권장)

프로젝트에는 서버 관리를 위한 편리한 스크립트가 포함되어 있습니다:

```bash
# 모든 서버 일괄 시작 (백그라운드)
./start_all_servers.sh

# 모든 서버 중지
./stop_all_servers.sh

# 개별 서버 시작 (포그라운드)
./start_api_server.sh    # API 서버 (port 8010)
./start_a2a_server_new.sh # A2A 서버 (port 8011)
```

**스크립트 기능:**
- 가상환경 자동 활성화
- .env 파일 검증
- 기존 프로세스 자동 정리
- Redis/Weaviate 상태 확인
- PID 파일 기반 프로세스 관리

**로그 확인:**
```bash
tail -f logs/api_server.log        # API 서버 로그
tail -f logs/a2a_server_*.log      # A2A 서버 로그
```

#### 수동 실행 방법

**REST API 서버 (port 8010):**
```bash
source venv/bin/activate
python main.py --mode server
```

**A2A 서버 (port 8011):**
```bash
source venv/bin/activate
python start_a2a_server.py
```

### 2. 대화형 모드

```bash
python main.py --mode interactive
```

### 3. 단일 쿼리 테스트

```bash
python main.py --mode test --query "시가총액 상위 10개 회사를 알려주세요"
```

### 4. API 엔드포인트 사용

#### 동기 쿼리 처리

```bash
curl -X POST "http://localhost:8010/query" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "시가총액 상위 10개 회사를 알려주세요",
       "session_id": "test_session",
       "user_id": "test_user"
     }'
```

#### 비동기 쿼리 처리

```bash
curl -X POST "http://localhost:8010/query/async" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "시가총액 상위 10개 회사를 알려주세요",
       "session_id": "test_session",
       "user_id": "test_user"
     }'
```

#### 헬스 체크

```bash
curl http://localhost:8010/health
```

#### 시스템 상태

```bash
curl http://localhost:8010/status
```

#### 동시성 상태 확인

```bash
# API 서버 동시성 상태
curl http://localhost:8010/concurrency/status

# A2A 서버 동시성 상태
curl http://localhost:8011/concurrency/status
```

#### 캐시 관리

```bash
# 캐시 통계 조회
curl http://localhost:8010/cache/stats

# 캐시 초기화
curl -X POST http://localhost:8010/cache/clear
```

#### 연결 풀 상태

```bash
# Weaviate 연결 풀 통계
curl http://localhost:8010/vector-store/pool/stats
```

#### A2A 프로토콜 테스트

```bash
# Agent Card 확인
curl http://localhost:8011/.well-known/agent.json

# 메시지 전송 테스트 (동기)
curl -X POST http://localhost:8011/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "test_123",
        "role": "user",
        "parts": [{"kind": "text", "text": "삼성전자 주가를 알려주세요"}]
      }
    },
    "id": 1
  }'

# 스트리밍 테스트
curl -X POST http://localhost:8011/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/stream",
    "params": {
      "message": {
        "messageId": "test_stream_456",
        "role": "user",
        "parts": [{"kind": "text", "text": "코스피 상위 10개 종목"}]
      }
    },
    "id": 2
  }'
```

### 5. Excel 배치 처리 (비동기)

여러 질의를 Excel 파일로 비동기 일괄 처리:

```bash
# 기본 사용법
python query_withexcel.py queries.xlsx

# 출력 파일 지정
python query_withexcel.py queries.xlsx --output results.xlsx

# 동시 처리 수 조정 (기본값: 5)
python query_withexcel.py queries.xlsx --concurrent 3

# 중간 저장 간격 변경 (기본값: 10)
python query_withexcel.py queries.xlsx --interval 20

# 예제 Excel 파일 생성
python query_withexcel.py --create-example
```

**Excel 파일 형식:**
- 필수 컬럼: `NO`, `질의`
- 결과 컬럼: `구문` (SQL), `구문O` (구문 체크 결과), `결과O` (실행 성공 여부)

**환경 변수:**
```bash
# Excel 배치 처리 전용 설정
EXCEL_MAX_CONCURRENT_QUERIES=5    # 최대 동시 처리 쿼리 수
EXCEL_QUERY_TIMEOUT=300           # 쿼리 타임아웃 (초)
```

**주요 기능:**
- **비동기 처리**: 여러 쿼리를 동시에 처리하여 속도 향상
- **동시성 제어**: 서버 부하 관리를 위한 동시 처리 수 제한
- **중간 저장**: 지정된 간격마다 자동 저장
- **통계 제공**: 처리 시간, 성공/실패 통계
- **기존 코드 호환**: `process_excel_batch()` 함수 유지

### 6. Jupyter Lab 실행

개발 및 분석을 위한 Jupyter Lab 환경:

```bash
# 방법 1: 스크립트 사용
./start_jupyter.sh

# 방법 2: 직접 실행
source venv/bin/activate
jupyter lab --port=8888

# 방법 3: 백그라운드 실행
nohup ./start_jupyter.sh > jupyter.log 2>&1 &
```

**Jupyter 설정:**
- 전용 커널: "M-Asset POC (Python 3.10)"
- 기본 포트: 8888
- 가상환경의 모든 패키지 사용 가능

## API 문서

### REST API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- Swagger UI: `http://localhost:8010/docs`
- ReDoc: `http://localhost:8010/redoc`

### A2A API 문서

- Agent Card: `http://localhost:8011/.well-known/agent.json`
- OpenAPI 문서: `http://localhost:8011/docs`

### 상세 기술 문서

- [A2A 아키텍처](docs/A2A_ARCHITECTURE.md)
- [Text2SQL 에이전트](docs/TEXT2SQL_AGENT.md)
- [벡터 스토어](docs/VECTOR_STORE.md)
- [Langfuse 통합](docs/LANGFUSE_INTEGRATION.md)
- [동시성 제어](docs/CONCURRENCY.md)
- [LLM 캐싱](docs/CACHING.md)
- [연결 풀링](docs/CONNECTION_POOLING.md)
- [서버 운영 가이드](docs/SERVER_OPERATIONS.md)
- [Docker 배포 가이드](DOCKER_USAGE.md)

## 데이터베이스 스키마

프로젝트는 다음 테이블들을 사용합니다:

- `industry_stock_mapping`: 업종별 종목 매핑 정보
- `exchange_kosdaq_stock_master`: 거래소 종목 마스터 정보
- `exchange_kosdaq_stock_master_01`: 상세 주가 정보
- `securities_stock_info_kospi/kosdaq`: 증권 종목 정보
- `daily_trade_execution_data`: 일별 체결 자료
- `trade_status`: 매매 현황
- `kospi/kosdaq_trade_execution`: 실시간 체결 정보

## 모듈별 설명

### Core 모듈 (`src/core/`)

- **config.py**: 전체 애플리케이션 설정 관리
- **database.py**: PostgreSQL 연결 및 관리 (asyncpg 사용)
- **vector_store.py**: Weaviate 벡터 스토어 관리
- **langfuse_manager.py**: Langfuse 추적 시스템 관리
- **concurrency_limiter.py**: 동시 요청 제한 및 대기열 관리
- **llm_cache_manager.py**: Redis 기반 LLM 응답 캐싱
- **weaviate_pool.py**: Weaviate 연결 풀 관리

### Agents 모듈 (`src/agents/`)

- **text_to_sql_agent.py**: LangGraph 기반 Text-to-SQL 에이전트

### API 모듈 (`src/api/`)

- **server.py**: FastAPI 기반 REST API 서버

### Utils 모듈 (`src/utils/`)

- **weaviate_setup.py**: Weaviate 초기 설정 및 데이터 삽입

## 개발 가이드

### 로깅

모든 주요 구성 요소에는 상세한 로깅이 구현되어 있습니다. 로그 레벨을 조정하려면 각 모듈의 로깅 설정을 수정하세요.

### 추적 시스템

Langfuse를 통해 모든 LLM 호출과 에이전트 실행이 추적됩니다. `session_id`와 `user_id`를 통해 사용자별 추적이 가능합니다.

### 에러 처리

각 구성 요소는 적절한 에러 처리와 재시도 로직을 포함하고 있습니다. 최대 재시도 횟수는 `MAX_TEXT_TO_SQL_RETRIES` 환경 변수로 설정할 수 있습니다.

#### 알려진 이슈 해결
- **SQL 쿼리 파싱 오류**: LLM 응답에서 SQL 추출 시 'sql' 키워드가 포함되는 문제
  - `text_to_sql_agent.py`의 `_extract_sql_from_response` 메서드 개선
  - 다양한 마크다운 코드 블록 패턴 지원 (```sql, `sql, ::sql 등)
  - 백틱 하나로 감싸진 SQL 쿼리 처리 추가
  - OpenAI 인터페이스 응답 객체 처리
- **SQL 실행 오류 자동 수정**: LLM이 에러를 분석하고 수정된 쿼리를 자동 재실행
  - PostgreSQL 오류 메시지와 힌트를 LLM에게 전달
  - 컬럼명, 테이블명 오류 자동 감지 및 수정
  - 최대 3회 재시도로 무한 루프 방지
  - 예시: `trade_volume` → `trading_volume` 자동 수정
- **재귀 한계 오류**: 벡터 DB 검색 실패 시 GraphRecursionError 발생
  - 기본 스키마 fallback 메커니즘 구현 (`default_schema.py`)
  - recursion_limit을 150으로 증가
- **Python 3.10 호환성**: asyncio.timeout 대신 asyncio.wait_for 사용

## 기술 스택

- **Backend**: FastAPI, Python 3.10+
- **Database**: PostgreSQL with AsyncPG
- **Vector Store**: Weaviate
- **LLM**: OpenAI API compatible (VLLM)
- **Embeddings**: Ollama (bge-m3)
- **Agent Framework**: LangGraph
- **Monitoring**: Langfuse
- **Caching**: Redis
- **Concurrency**: asyncio, threading
- **Development**: Jupyter Lab, pytest
- **Containerization**: Docker, Docker Compose

## Docker 배포

### 빠른 시작

```bash
# 1. Docker Compose로 빌드 및 실행
docker-compose up -d

# 2. 컨테이너 접속
docker exec -it m-asset-poc bash

# 3. 서버 실행
./start_all_servers.sh     # API + A2A 서버
./start_jupyter.sh         # Jupyter Lab (선택적)
```

### 포트 정보

| 서비스 | 포트 | 접속 URL |
|--------|------|----------|
| API 서버 | 8010 | http://localhost:8010 |
| A2A 서버 | 8011 | http://localhost:8011 |
| Jupyter Lab | 8888 | http://localhost:8888 |

### 상세 사용법

Docker 관련 상세 사용법은 [DOCKER_USAGE.md](DOCKER_USAGE.md)를 참조하세요.

## 라이선스

이 프로젝트는 내부 POC 목적으로 개발되었습니다.