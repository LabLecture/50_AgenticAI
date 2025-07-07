"""
벡터 DB 연결 및 쿼리 테스트
"""
from src.core.vector_store import vector_store_manager

# 벡터 스토어 초기화
try:
    vector_store_manager.initialize()
    print("벡터 스토어 초기화 성공")
except Exception as e:
    print(f"벡터 스토어 초기화 실패: {e}")
    exit(1)

# 테스트 쿼리들
test_queries = [
    "삼성전자의 현재 주가는 얼마인가요?",
    "삼성전자 주가",
    "삼성전자",
    "주가"
]

print("\n샘플 쿼리 검색 테스트:")
print("-" * 50)

for query in test_queries:
    try:
        # max_distance를 늘려서 더 많은 결과 가져오기
        samples = vector_store_manager.search_sample_queries(query, limit=5, max_distance=2.0)
        print(f"\n쿼리: '{query}'")
        print(f"검색 결과 수: {len(samples)}")
        if samples:
            print("첫 번째 샘플:")
            for sample in samples[:2]:
                print(f"  - Explanation: {sample.get('explanation', 'N/A')}")
                print(f"  - SQL: {sample.get('query', 'N/A')[:100]}...")
    except Exception as e:
        print(f"검색 실패: {e}")

print("\n\n스키마 검색 테스트:")
print("-" * 50)

try:
    schema = vector_store_manager.search_schema_examples("삼성전자", limit=5)
    print(f"스키마 검색 결과: {schema[:200]}...")
except Exception as e:
    print(f"스키마 검색 실패: {e}")

# Weaviate 컬렉션 정보 확인
print("\n\nWeaviate 컬렉션 정보:")
print("-" * 50)
try:
    client = vector_store_manager._client
    collections = client.collections.list_all()
    print(f"사용 가능한 컬렉션: {collections}")
    
    # 샘플 컬렉션 확인
    sample_collection_name = "M_asset_sample_query_2_hint"
    if client.collections.exists(sample_collection_name):
        sample_collection = client.collections.get(sample_collection_name)
        count = sample_collection.aggregate.over_all(total_count=True)
        print(f"\n'{sample_collection_name}' 컬렉션:")
        print(f"  - 총 문서 수: {count.total_count}")
        
        # 몇 개 샘플 가져오기
        samples = sample_collection.query.fetch_objects(limit=3)
        print(f"  - 샘플 데이터:")
        for i, obj in enumerate(samples.objects):
            print(f"    {i+1}. {obj.properties}")
    else:
        print(f"'{sample_collection_name}' 컬렉션이 존재하지 않습니다.")
        
except Exception as e:
    print(f"컬렉션 정보 확인 실패: {e}")