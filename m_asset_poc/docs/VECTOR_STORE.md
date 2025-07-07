# Vector Store 기술 문서

## 개요

Vector Store는 Weaviate를 사용하여 SQL 쿼리 샘플을 벡터화하고 유사성 검색을 통해 Text2SQL 성능을 향상시키는 모듈입니다.

## 구조 (`src/core/vector_store.py`)

### 주요 클래스

#### VectorStore

벡터 데이터베이스 관리 및 검색 기능을 제공하는 메인 클래스

**주요 속성:**
- `client`: Weaviate 클라이언트
- `collection_name`: 컬렉션 이름 ("QuerySamples")
- `_embeddings`: Ollama 임베딩 모델 (nomic-embed-text)

### 핵심 기능

#### 1. 초기화 및 연결

```python
def __init__(self):
    """벡터 스토어 초기화"""
    try:
        import weaviate
        self.client = weaviate.connect_to_custom(
            http_host=config.weaviate.host,
            http_port=config.weaviate.port,
            http_secure=config.weaviate.secure,
            grpc_host=config.weaviate.host,
            grpc_port=config.weaviate.grpc_port,
            grpc_secure=config.weaviate.secure
        )
        
        self._embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url=config.ollama.base_url
        )
        
    except ImportError:
        logger.warning("Weaviate not available")
        self.client = None
```

#### 2. 컬렉션 관리

**컬렉션 생성:**
```python
def create_collection(self):
    """QuerySamples 컬렉션 생성"""
    if not self.is_available():
        return False
    
    try:
        collection = self.client.collections.create(
            name=self.collection_name,
            properties=[
                weaviate.classes.config.Property(
                    name="query",
                    data_type=weaviate.classes.config.DataType.TEXT,
                    description="User natural language query"
                ),
                weaviate.classes.config.Property(
                    name="sql",
                    data_type=weaviate.classes.config.DataType.TEXT,
                    description="Corresponding SQL query"
                ),
                weaviate.classes.config.Property(
                    name="table_info",
                    data_type=weaviate.classes.config.DataType.TEXT,
                    description="Related table information"
                )
            ],
            vectorizer_config=weaviate.classes.config.Configure.Vectorizer.none()
        )
```

**컬렉션 삭제:**
```python
def delete_collection(self):
    """기존 컬렉션 삭제"""
    if self.client.collections.exists(self.collection_name):
        self.client.collections.delete(self.collection_name)
```

#### 3. 데이터 추가

**단일 샘플 추가:**
```python
def add_query_sample(self, query: str, sql: str, table_info: str = ""):
    """쿼리 샘플을 벡터 스토어에 추가"""
    if not self.is_available():
        return False
    
    try:
        # 임베딩 생성
        vector = self._embeddings.embed_query(query)
        
        # 데이터 추가
        collection = self.client.collections.get(self.collection_name)
        collection.data.insert(
            properties={
                "query": query,
                "sql": sql,
                "table_info": table_info
            },
            vector=vector
        )
        return True
    except Exception as e:
        logger.error(f"Error adding query sample: {e}")
        return False
```

**배치 추가:**
```python
def add_multiple_samples(self, samples: List[Dict[str, str]]):
    """여러 샘플을 배치로 추가"""
    if not self.is_available():
        return False
    
    try:
        collection = self.client.collections.get(self.collection_name)
        
        with collection.batch.dynamic() as batch:
            for sample in samples:
                vector = self._embeddings.embed_query(sample["query"])
                batch.add_object(
                    properties={
                        "query": sample["query"],
                        "sql": sample["sql"],
                        "table_info": sample.get("table_info", "")
                    },
                    vector=vector
                )
        return True
    except Exception as e:
        logger.error(f"Error adding multiple samples: {e}")
        return False
```

#### 4. 유사성 검색

```python
def search_similar_queries(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """유사한 쿼리 검색"""
    if not self.is_available():
        return []
    
    try:
        # 쿼리 임베딩 생성
        query_vector = self._embeddings.embed_query(query)
        
        # 벡터 검색 수행
        collection = self.client.collections.get(self.collection_name)
        response = collection.query.near_vector(
            near_vector=query_vector,
            limit=limit,
            return_metadata=weaviate.classes.query.MetadataQuery(
                distance=True,
                certainty=True
            )
        )
        
        # 결과 포맷팅
        results = []
        for obj in response.objects:
            results.append({
                "query": obj.properties["query"],
                "sql": obj.properties["sql"],
                "table_info": obj.properties["table_info"],
                "distance": obj.metadata.distance,
                "certainty": obj.metadata.certainty
            })
        
        return results
    except Exception as e:
        logger.error(f"Error searching similar queries: {e}")
        return []
```

## 설정 및 환경

### 환경 변수 (.env)

```env
# Weaviate 설정
WEAVIATE_ENABLED=true
WEAVIATE_HOST=192.168.1.203
WEAVIATE_PORT=8585
WEAVIATE_GRPC_PORT=50051
WEAVIATE_SECURE=false

# Ollama 설정  
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# 선택적 사용
VECTOR_STORE_OPTIONAL=true
```

### 설정 클래스 (`src/core/config.py`)

```python
@dataclass
class WeaviateConfig:
    enabled: bool = True
    host: str = "localhost"
    port: int = 8080
    grpc_port: int = 50051
    secure: bool = False

@dataclass
class OllamaConfig:
    base_url: str = "http://localhost:11434"
    embedding_model: str = "nomic-embed-text"
```

## 샘플 데이터 구조

### QuerySamples 스키마

```json
{
  "class": "QuerySamples",
  "properties": [
    {
      "name": "query",
      "dataType": ["text"],
      "description": "사용자 자연어 질의"
    },
    {
      "name": "sql", 
      "dataType": ["text"],
      "description": "해당 SQL 쿼리"
    },
    {
      "name": "table_info",
      "dataType": ["text"], 
      "description": "관련 테이블 정보"
    }
  ]
}
```

### 샘플 데이터 예시

```python
samples = [
    {
        "query": "삼성전자 주가를 알려주세요",
        "sql": "SELECT symbol, price, volume FROM stock_prices WHERE symbol = '005930' ORDER BY date DESC LIMIT 1",
        "table_info": "stock_prices: symbol(종목코드), price(가격), volume(거래량), date(날짜)"
    },
    {
        "query": "코스피 상위 10개 종목을 보여주세요",
        "sql": "SELECT symbol, company_name, market_cap FROM companies WHERE market = 'KOSPI' ORDER BY market_cap DESC LIMIT 10",
        "table_info": "companies: symbol(종목코드), company_name(회사명), market_cap(시가총액), market(시장)"
    }
]
```

## 초기 데이터 설정

### Jupyter 노트북 활용 (`Weaviate_table_info_masset1.ipynb`)

원래 Jupyter 노트북에서 추출한 테이블 정보와 샘플 쿼리를 벡터 스토어에 초기화:

```python
def setup_initial_data():
    """초기 벡터 데이터 설정"""
    vector_store = VectorStore()
    
    if not vector_store.is_available():
        logger.warning("Vector store not available")
        return
    
    # 기존 컬렉션 삭제 후 재생성
    vector_store.delete_collection()
    vector_store.create_collection()
    
    # 샘플 데이터 추가
    samples = load_sample_queries()  # JSON 파일에서 로드
    vector_store.add_multiple_samples(samples)
    
    logger.info(f"Added {len(samples)} query samples to vector store")
```

## Text2SQL Agent 통합

### 검색 및 컨텍스트 활용

```python
# Text2SQL Agent에서 벡터 검색 활용
def get_sample_query_from_vector_db(state: TextToSqlState):
    """벡터 DB에서 유사 쿼리 검색"""
    try:
        if vector_store and vector_store.is_available():
            similar_queries = vector_store.search_similar_queries(
                query=state["user_query"],
                limit=3
            )
            
            # 검색 결과를 컨텍스트로 포맷팅
            context = ""
            for result in similar_queries:
                if result["certainty"] > 0.7:  # 신뢰도 임계값
                    context += f"Query: {result['query']}\n"
                    context += f"SQL: {result['sql']}\n\n"
            
            return {
                **state,
                "sample_queries": context
            }
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        
    return {
        **state,
        "sample_queries": ""
    }
```

## 성능 최적화

### 1. 임베딩 캐싱

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_embedding(query: str):
    """임베딩 결과 캐싱"""
    return self._embeddings.embed_query(query)
```

### 2. 배치 처리

```python
def batch_add_samples(self, samples: List[Dict], batch_size: int = 100):
    """대용량 데이터 배치 처리"""
    for i in range(0, len(samples), batch_size):
        batch = samples[i:i + batch_size]
        self.add_multiple_samples(batch)
        logger.info(f"Processed batch {i//batch_size + 1}")
```

### 3. 연결 관리

```python
def __enter__(self):
    """컨텍스트 매니저 진입"""
    return self

def __exit__(self, exc_type, exc_val, exc_tb):
    """리소스 정리"""
    if self.client:
        self.client.close()
```

## 모니터링 및 디버깅

### 검색 성능 메트릭

```python
def get_search_metrics(self) -> Dict[str, Any]:
    """검색 성능 메트릭 수집"""
    try:
        collection = self.client.collections.get(self.collection_name)
        
        # 컬렉션 통계
        response = collection.aggregate.over_all(
            total_count=True
        )
        
        return {
            "total_documents": response.total_count,
            "collection_name": self.collection_name,
            "embedding_model": "nomic-embed-text",
            "status": "healthy"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

### 로깅

```python
import logging
logger = logging.getLogger(__name__)

# 검색 로깅
logger.info(f"Vector search for: {query}")
logger.debug(f"Found {len(results)} similar queries")
logger.warning("Vector store not available, skipping search")
```

## 알려진 제한사항

1. **의존성**: Weaviate 서버가 실행 중이어야 함
2. **임베딩 모델**: Ollama nomic-embed-text 모델 필요
3. **메모리**: 대용량 벡터 데이터 시 메모리 사용량 증가
4. **네트워크**: Weaviate 서버 연결 상태에 의존

## 향후 개선 계획

1. **다양한 임베딩 모델**: OpenAI, Sentence-BERT 지원
2. **하이브리드 검색**: 키워드 + 벡터 검색 결합
3. **자동 인덱싱**: 새로운 쿼리 자동 학습
4. **성능 최적화**: 근사 최근접 이웃(ANN) 알고리즘 적용
5. **분산 처리**: 다중 Weaviate 인스턴스 지원