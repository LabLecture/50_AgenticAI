# M-Asset POC (증권 종목 에이전트)

증권 종목 관련 자연어 질의를 SQL로 변환하고 실행하는 마켓 에이전트 POC 프로젝트입니다.

## 주요 기능

- **Text-to-SQL 변환**: 자연어 질의를 PostgreSQL 쿼리로 자동 변환
- **벡터 검색**: Weaviate를 이용한 스키마 및 샘플 쿼리 검색 (선택적)
- **LangGraph 에이전트**: 다단계 쿼리 생성 및 검증 워크플로
- **추적 시스템**: Langfuse를 이용한 실행 추적 및 모니터링 (선택적)
- **REST API**: FastAPI 기반 웹 서비스
- **Excel 배치 처리**: 여러 질의를 Excel 파일로 일괄 처리 및 결과 저장

## 시스템 구조

```
├── src/                           # 소스 코드
│   ├── core/                      # 핵심 구성 요소
│   │   ├── config.py              # 설정 관리
│   │   ├── database.py            # 데이터베이스 연결 (asyncpg)
│   │   ├── vector_store.py        # Weaviate 벡터 스토어 관리
│   │   └── langfuse_manager.py    # Langfuse 추적 시스템
│   ├── agents/                    # 에이전트 모듈
│   │   └── text_to_sql_agent.py   # LangGraph 기반 Text-to-SQL 에이전트
│   ├── api/                       # API 서버
│   │   └── server.py              # FastAPI 서버
│   └── utils/                     # 유틸리티
│       └── weaviate_setup.py      # Weaviate 초기 설정
├── main.py                        # 메인 엔트리 포인트
├── query_withexcel.py             # Excel 파일 배치 처리
└── requirements.txt               # 의존성 패키지
```

## 설치 및 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하거나 환경 변수를 설정하세요:

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
```

### 3. Weaviate 벡터 스토어 초기 설정

```bash
python main.py --mode setup
```

## 사용 방법

### 1. API 서버 실행

```bash
python main.py --mode server
```

서버는 기본적으로 `http://localhost:8010`에서 실행됩니다.

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

### 5. Excel 배치 처리

여러 질의를 Excel 파일로 일괄 처리하려면:

```python
from src.agents.text_to_sql_agent import text_to_sql_agent
from query_withexcel import process_excel_batch

# Excel 파일 처리
process_excel_batch(
    excel_file_path="queries.xlsx",  # 입력 파일 (NO, 질의 컬럼 필수)
    text_to_sql_app=text_to_sql_agent.app,
    output_file_path="results.xlsx"  # 출력 파일 (선택사항)
)
```

Excel 파일 형식:
- 필수 컬럼: `NO`, `질의`
- 결과 컬럼: `구문` (SQL), `구문O` (구문 체크 결과), `결과O` (실행 성공 여부)

**실행 예제:**
```bash
# 가상환경 활성화
source venv/bin/activate

# Excel 배치 처리 실행
python query_withexcel.py example_queries.xlsx --output my_results.xlsx

# 또는 main.py를 통한 실행
python main.py --mode excel --input example_queries.xlsx --output my_results.xlsx
```

## API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- Swagger UI: `http://localhost:8010/docs`
- ReDoc: `http://localhost:8010/redoc`

## 데이터베이스 스키마

프로젝트는 다음 테이블들을 사용합니다:

- `industry_stock_mapping`: 업종별 종목 매핑 정보
- `exchange_kosdaq_stock_master`: 거래소 종목 마스터 정보
- `exchange_kosdaq_stock_master_01`: 상세 주가 정보
- `securities_stock_info_kospi/kosdaq`: 증권 종목 정보
- `daily_trade_execution_data`: 일별 체결 자료
- `trade_status`: 매매 현황
- `kospi/kosdaq_trade_execution`: 실시간 체결 정보

## 개발 가이드

### 로깅

모든 주요 구성 요소에는 상세한 로깅이 구현되어 있습니다. 로그 레벨을 조정하려면 각 모듈의 로깅 설정을 수정하세요.

### 추적 시스템

Langfuse를 통해 모든 LLM 호출과 에이전트 실행이 추적됩니다. `session_id`와 `user_id`를 통해 사용자별 추적이 가능합니다.

### 에러 처리

각 구성 요소는 적절한 에러 처리와 재시도 로직을 포함하고 있습니다. 최대 재시도 횟수는 `MAX_TEXT_TO_SQL_RETRIES` 환경 변수로 설정할 수 있습니다.

## 라이선스

이 프로젝트는 내부 POC 목적으로 개발되었습니다.

## 기여

개발팀 내부에서만 기여가 가능합니다.