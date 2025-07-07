"""
Weaviate setup and data initialization module.
Handles collection creation and schema data insertion.
"""

import weaviate
from weaviate.classes.config import Property, DataType, Configure
from langchain_community.embeddings import OllamaEmbeddings
from typing import Dict, List, Any
import logging

from ..core.config import config

logger = logging.getLogger(__name__)


class WeaviateSetup:
    """Weaviate 초기 설정 및 데이터 삽입 클래스"""
    
    def __init__(self):
        """Weaviate 설정 클래스 초기화"""
        self._client = None
        self._embeddings = None
        
    def initialize(self):
        """Weaviate 클라이언트 및 임베딩 초기화"""
        try:
            # Weaviate 클라이언트 초기화
            self._client = weaviate.connect_to_local(
                host=config.weaviate.host,
                port=config.weaviate.port
            )
            
            # Ollama 임베딩 초기화
            self._embeddings = OllamaEmbeddings(
                base_url=config.ollama.base_url,
                model=config.ollama.embedding_model
            )
            
            logger.info("Weaviate setup initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Weaviate setup: {e}")
            raise
    
    def check_existing_collections(self) -> bool:
        """기존 컬렉션 존재 여부 확인"""
        if self._client is None:
            self.initialize()
        
        try:
            existing_collections = self._client.collections.list_all()
            schema_collection_exists = config.weaviate.schema_collection in existing_collections
            sample_collection_exists = config.weaviate.sample_collection in existing_collections
            
            logger.info(f"Schema collection '{config.weaviate.schema_collection}' exists: {schema_collection_exists}")
            logger.info(f"Sample collection '{config.weaviate.sample_collection}' exists: {sample_collection_exists}")
            
            if schema_collection_exists:
                # 컬렉션에 데이터가 있는지 확인
                try:
                    collection = self._client.collections.get(config.weaviate.schema_collection)
                    # 첫 번째 객체 가져와보기
                    results = collection.query.fetch_objects(limit=1)
                    has_data = len(results.objects) > 0
                    logger.info(f"Schema collection has data: {has_data}")
                    return has_data
                except Exception as e:
                    logger.warning(f"Error checking collection data: {e}")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking existing collections: {e}")
            return False
    
    def create_schema_collection(self, collection_name: str = None, force_recreate: bool = False) -> bool:
        """스키마 컬렉션 생성"""
        if self._client is None:
            self.initialize()
        
        collection_name = collection_name or config.weaviate.schema_collection
        
        try:
            # 기존 컬렉션 확인
            existing_collections = self._client.collections.list_all()
            if collection_name in existing_collections:
                if not force_recreate:
                    logger.info(f"Collection '{collection_name}' already exists. Skipping creation.")
                    return True
                else:
                    # 강제 재생성일 때만 삭제
                    self._client.collections.delete(name=collection_name)
                    logger.info(f"Deleted existing collection: {collection_name}")
            
            # 스키마 정의
            properties = [
                Property(name="query", data_type=DataType.TEXT),
                Property(name="type_name", data_type=DataType.TEXT),
                Property(name="explanation", data_type=DataType.TEXT),
                Property(name="search_content", data_type=DataType.TEXT),
            ]
            
            # 컬렉션 생성
            self._client.collections.create(
                name=collection_name,
                properties=properties,
                vectorizer_config=None,  # 벡터화를 직접 처리
                # Hybrid 검색을 위한 인덱스 설정
                inverted_index_config=Configure.inverted_index(
                    bm25_b=0.75,
                    bm25_k1=1.2,
                    index_null_state=False,
                    index_property_length=False,
                    index_timestamps=False,
                )
            )
            
            logger.info(f"Created collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating schema collection: {e}")
            return False
    
    def insert_table_schema_data(self, collection_name: str = None) -> bool:
        """테이블 스키마 데이터 삽입"""
        if self._client is None:
            self.initialize()
        
        collection_name = collection_name or config.weaviate.schema_collection
        
        try:
            collection = self._client.collections.get(collection_name)
            
            # 테이블 스키마 데이터 정의
            table_schemas = self._get_table_schema_data()
            
            inserted_count = 0
            for schema_data in table_schemas:
                # 임베딩 생성
                embedding = self._embeddings.embed_query(schema_data["search_content"])
                
                # 데이터 삽입
                uuid = collection.data.insert(
                    properties={
                        "query": schema_data["query"],
                        "type_name": schema_data["type_name"],
                        "explanation": schema_data["explanation"],
                        "search_content": schema_data["search_content"]
                    },
                    vector=embedding
                )
                
                logger.info(f"Inserted schema data for {schema_data['type_name']}: {uuid}")
                inserted_count += 1
            
            logger.info(f"Successfully inserted {inserted_count} table schema records")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting table schema data: {e}")
            return False
    
    def _get_table_schema_data(self) -> List[Dict[str, Any]]:
        """테이블 스키마 데이터 반환"""
        return [
            {
                "type_name": "업종_종목코드 매핑",
                "query": """
CREATE TABLE m_asset.industry_stock_mapping (
    industry_code VARCHAR(10),  -- 업종 코드
    stock_code VARCHAR(10),     -- 종목 코드
    market_type VARCHAR(20),    -- 시장 구분 (예: KOSPI, KOSDAQ, KONEX)
    data_date DATE,             -- 자료 일자
    listed_shares BIGINT,       -- 상장 주식 수
    index_shares BIGINT,        -- 지수 산정용 발행 주식 수
    market_cap BIGINT,          -- 시가총액 (상장주식수 * 수정주가)
    PRIMARY KEY (industry_code, stock_code, data_date),
    FOREIGN KEY(stock_code, data_date) REFERENCES m_asset.exchange_kosdaq_stock_master(stock_code, data_date)
);
                """,
                "explanation": "시장 구분 (예: KOSPI, KOSDAQ, KONEX), 지수 산정용 발행 주식 수, 시가총액",
                "search_content": "테이블 이름: 업종_종목코드 매핑. 설명: 시장 구분 (예: KOSPI, KOSDAQ, KONEX), 지수 산정용 발행 주식 수, 시가총액. 주요 내용: 이 테이블은 산업별 종목 코드를 매핑하며, 주식 시장의 상장 주식 수, 지수 산정용 발행 주식 수, 그리고 중요한 **시가총액** 정보를 포함합니다. 시가총액은 상장주식수와 수정주가를 곱한 값입니다. 이 테이블을 통해 **시가총액** 같은 정보를 찾을 수 있습니다."
            },
            {
                "type_name": "거래소_코스닥_종목_마스터",
                "query": """
CREATE TABLE m_asset.exchange_kosdaq_stock_master (
    stock_code VARCHAR(20),                         -- 종목코드
    short_code VARCHAR(20),                         -- 종목단축코드
    eng_symbol VARCHAR(50),                         -- 영문심볼
    market_type VARCHAR(20),                        -- 시장구분
    data_date DATE,                                 -- 자료일자
    kor_name_large VARCHAR(100),                    -- 종목한글명대
    kor_name_mid VARCHAR(100),                      -- 종목한글명중
    kor_name_small VARCHAR(100),                    -- 종목한글명소
    eng_name_large VARCHAR(100),                    -- 종목영문명대
    eng_name VARCHAR(100),                          -- 종목영문명
    listed_shares BIGINT,                           -- 상장주식수
    capital BIGINT,                                 -- 자본금
    face_value BIGINT,                              -- 종목액면가
    listing_date DATE,                              -- 상장일자
    settlement_month VARCHAR(10),                   -- 결산월
    regular_trading_unit BIGINT,                    -- 정규장매매수량단위
    after_hour_trading_unit BIGINT,                 -- 시간외매매수량단위
    annual_cum_trade_qty BIGINT,                    -- 연누적체결수량
    annual_cum_trade_amt BIGINT,                    -- 연누적거래대금
    short_sell_volume BIGINT,                       -- 공매도거래량
    short_sell_amount BIGINT,                       -- 공매도거래대금
    preferred_stock_type_code VARCHAR(10),          -- 우선주구분코드
    backdoor_listing_flag CHAR(1),                  -- 우회상장여부
    national_stock_flag CHAR(1),                    -- 국민주여부
    spc_flag CHAR(1),                               -- 기업인수목적회사여부
    trading_halt_flag CHAR(1),                      -- 거래정지여부
    trading_halt_reason_code VARCHAR(10),           -- 거래정지사유코드
    management_stock_flag CHAR(1),                  -- 관리종목여부
    market_warning_risk_alert_flag CHAR(1),         -- 시장경보위험예고여부
    market_warning_type_code VARCHAR(10),           -- 시장경보구분코드
    market_warning_data_date DATE,                  -- 시장경고자료일자
    unfaithful_disclosure_flag CHAR(1),             -- 불성실공시지정여부
    unfaithful_disclosure_designation_date DATE,    -- 불성실공시법인지정일
    unfaithful_disclosure_release_date DATE,        -- 불성실공시법인해제일
    liquidation_trading_flag CHAR(1),               -- 정리매매여부
    after_hours_trading_flag CHAR(1),               -- 시간외매매가능여부
    short_selling_flag CHAR(1),                     -- 공매도가능여부
    margin_order_flag CHAR(1),                      -- 신용주문가능여부
    deficit_flag CHAR(1),                           -- 결손여부
    earnings_per_share BIGINT,                      -- 주당순이익(원)
    prev_year_per DOUBLE PRECISION,                 -- 전기PER
    half_year_per DOUBLE PRECISION,                 -- 반기PER
    book_value_per_share BIGINT,                    -- 주당순자산가치(원)
    book_value_ratio DOUBLE PRECISION,              -- 주당순자산비율
    dividend_per_share BIGINT,                      -- 주당배당금
    dividend_yield DOUBLE PRECISION,                -- 배당수익률
    investment_caution_flag CHAR(1),                -- 투자주의환기종목여부
    investment_caution_date DATE,                   -- 투자주의환기일자
    margin_trading_available_flag CHAR(1),          -- 신용거래가능구분
    short_term_overheating_flag CHAR(1),            -- 단기과열지정구분
    short_term_overheating_start_date DATE,         -- 단기과열지정일자
    short_term_overheating_end_date DATE,           -- 단기과열종료일자
    illiquid_stock_flag CHAR(1),                    -- 저유동성 종목 여부
    PRIMARY KEY (stock_code, short_code, data_date)
);
                """,
                "explanation": "종목한글명, 종목영문명, 상장주식수, 자본금, 종목액면가, 평가가격, 상장일자, 결산월, 정규장매매수량단위, 시간외매매수량단위, 연누적체결수량, 연누적거래대금, 공매도거래량, 공매도거래대금, 우선주구분코드, 우회상장여부, 국민주여부, 기업인수목적회사여부, 거래정지여부, 거래정지사유코드, 관리종목여부, 시장경보위험예고여부, 시장경보구분코드, 시장경고자료일자, 불성실공시지정여부, 불성실공시법인지정일, 불성실공시법인해제일, 정리매매여부, 시간외매매가능여부, 공매도가능여부, 신용주문가능여부, 결손여부, 주당순이익, 전기PER, 반기PER, 주당순자산가치, 주당순자산비율, 주당배당금, 배당수익률, 투자주의환기종목여부, 투자주의환기일자, 신용거래가능구분, 단기과열지정구분, 단기과열지정일자, 단기과열종료일자, 저유동성 종목 여부",
                "search_content": "테이블 이름: 거래소_코스닥_종목_마스터. 설명: 종목한글명, 종목영문명, 상장주식수, 자본금, 종목액면가, 평가가격, 상장일자, 결산월, 정규장매매수량단위, 시간외매매수량단위, 연누적체결수량, 연누적거래대금, 공매도거래량, 공매도거래대금, 우선주구분코드, 우회상장여부, 국민주여부, 기업인수목적회사여부, 거래정지여부, 거래정지사유코드, 관리종목여부, 시장경보위험예고여부, 시장경보구분코드, 시장경고자료일자, 불성실공시지정여부, 불성실공시법인지정일, 불성실공시법인해제일, 정리매매여부, 시간외매매가능여부, 공매도가능여부, 신용주문가능여부, 결손여부, 주당순이익, 전기PER, 반기PER, 주당순자산가치, 주당순자산비율, 주당배당금, 배당수익률, 투자주의환기종목여부, 투자주의환기일자, 신용거래가능구분, 단기과열지정구분, 단기과열지정일자, 단기과열종료일자, 저유동성 종목 여부. 주요 내용: 이 테이블은 산업별 종목 코드를 매핑하며, **회사명, 종목명**, 상장주식수, 자본금, PER, 주당순이익, 주당순자산가치, 배당수익률 등의 정보를 찾을 수 있습니다."
            },
            {
                "type_name": "거래소_코스닥_종목_마스터_01",
                "query": """
CREATE TABLE m_asset.exchange_kosdaq_stock_master_01 (
    data_date DATE,                                -- 자료일자
    prev_trading_amount BIGINT,                    -- 전일거래대금
    base_price BIGINT,                             -- 기준가
    upper_limit_price BIGINT,                      -- 상한가
    lower_limit_price BIGINT,                      -- 하한가
    process_time VARCHAR(10),                      -- 처리시간
    close_price BIGINT,                            -- 종가(현재가)
    prev_comparison_type VARCHAR(10),              -- 전일대비구분
    prev_comparison_amount BIGINT,                 -- 전일대비금액
    open_price BIGINT,                             -- 시가
    high_price BIGINT,                             -- 고가
    low_price BIGINT,                              -- 저가
    trading_volume BIGINT,                         -- 거래량
    trading_amount BIGINT,                         -- 거래대금
    open_time VARCHAR(10),                         -- 시가시간
    high_time VARCHAR(10),                         -- 고가시간
    low_time VARCHAR(10),                          -- 저가시간
    ask_price BIGINT,                              -- 매도호가
    bid_price BIGINT,                              -- 매수호가
    market_time_type VARCHAR(10),                  -- 시장시간구분
    single_price_extension_type VARCHAR(10),       -- 단일가매매연장구분
    same_time_tick_count INT,                      -- 동일시간틱건수
    execution_strength_type VARCHAR(10),           -- 체결강도구분 0:초기값
    bid_volume BIGINT,                             -- 매수거래량
    ask_volume BIGINT,                             -- 매도거래량
    yearly_high_price BIGINT,                      -- 연중최고가
    yearly_high_date DATE,                         -- 연중최고일자
    yearly_low_price BIGINT,                       -- 연중최저가
    yearly_low_date DATE,                          -- 연중최저일자
    yearly_high_trading_day DATE,                  -- 연중최고거래일
    listing_high_trading_day DATE,                 -- 상장최고거래일
    yearly_high_volume BIGINT,                     -- 연중최고거래량
    listing_high_volume BIGINT,                    -- 상장최고거래량
    yearly_low_trading_day DATE,                   -- 연중최저거래일
    listing_low_trading_day DATE,                  -- 상장최저거래일
    yearly_low_volume BIGINT,                      -- 연중최저거래량
    listing_low_volume BIGINT,                     -- 상장최저거래량
    listing_highest_price BIGINT,                  -- 상장중최고가
    listing_highest_date DATE,                     -- 상장중최고일자
    listing_lowest_price BIGINT,                   -- 상장중최저가
    listing_lowest_date DATE,                      -- 상장중최저일자
    high_52w_price BIGINT,                         -- 52주최고가
    high_52w_date DATE,                            -- 52주최고일자
    low_52w_price BIGINT,                          -- 52주최저가
    low_52w_date DATE,                             -- 52주최저일자
    high_52w_volume BIGINT,                        -- 52주최고거래량
    low_52w_volume BIGINT,                         -- 52주최저거래량
    high_52w_volume_date DATE,                     -- 52주최고거래량일자
    low_52w_volume_date DATE,                      -- 52주최저거래량일자
    prev_foreigner_data_date DATE,                 -- 전일외국인자료일자
    foreigner_limit_shares BIGINT,                 -- 외국인한도주식수
    foreigner_orderable_shares BIGINT,             -- 외국인주문가능주식수
    foreigner_limit_ratio DOUBLE PRECISION,        -- 외국인한도비율
    foreigner_holding_shares BIGINT,               -- 외국인보유주식수
    pre_market_off_close_volume BIGINT,            -- 장개시전시간외종가 거래량
    pre_market_off_close_amount BIGINT,            -- 장개시전시간외종가 거래대금
    pre_market_off_close_large_volume BIGINT,      -- 장개시전시간외종가 대량거래량
    pre_market_off_close_large_amount BIGINT,      -- 장개시전시간외종가 대량거래대금
    pre_market_off_close_basket_volume BIGINT,     -- 장개시전시간외종가 바스켓거래량
    pre_market_off_close_basket_amount BIGINT,     -- 장개시전시간외종가 바스켓거래대금
    pre_market_off_close_competition_large_volume BIGINT, -- 장개시전시간외종가 경쟁대량거래량
    pre_market_total_volume BIGINT,                -- 시간전전체거래량
    pre_market_total_amount BIGINT,                -- 시간전전체거래대금
    intraday_large_volume BIGINT,                  -- 장중대량거래량
    intraday_large_amount BIGINT,                  -- 장중대량거래대금
    after_market_off_close_volume BIGINT,          -- 장종료후시간외종가 거래량
    after_market_off_close_amount BIGINT,          -- 장종료후시간외종가 거래대금
    after_market_off_close_large_volume BIGINT,    -- 장종료후시간외종가 대량거래량
    after_market_off_close_large_amount BIGINT,    -- 장종료후시간외종가 대량거래대금
    stock_code VARCHAR(20),                        -- 종목코드
    market_type VARCHAR(10),                       -- 시장구분
    prev_close_price BIGINT,                       -- 전일종가
    prev_trading_volume BIGINT,                    -- 전일거래량
    PRIMARY KEY (stock_code, data_date),
    FOREIGN KEY(stock_code, data_date) REFERENCES m_asset.exchange_kosdaq_stock_master(stock_code, data_date)
);
                """,
                "explanation": "전일거래대금, 기준가, 상한가, 하한가, 처리시간, 종가(현재가), 전일대비구분, 전일대비금액, 시가, 고가, 저가, 거래량, 거래대금, 시가시간, 고가시간, 저가시간, 호가, 시장시간구분, 단일가매매연장구분, 동일시간틱건수, 체결강도, 연중최고가, 연중최저가, 연중최고거래량, 상장최고거래량, 연중최저거래량, 상장최저거래량, 상장중최고가, 상장중최저가, 52주최고가, 52주최저가, 52주최고거래량, 52주최저거래량, 전일외국인자료일자, 외국인한도주식수, 외국인주문가능주식수, 외국인한도비율, 외국인보유주식수, 장개시전시간외종가, 시간전전체거래량, 장중대량거래량, 장종료후시간외종가 거래량, 장종료후시간외종가 대량거래량, 시장구분, 전일종가, 전일거래량",
                "search_content": "테이블 이름: 거래소_코스닥_종목_마스터_01. 설명: 전일거래대금, 기준가, 상한가, 하한가, 처리시간, 종가(현재가), 전일대비구분, 전일대비금액, 시가, 고가, 저가, 거래량, 거래대금, 시가시간, 고가시간, 저가시간, 호가, 시장시간구분, 단일가매매연장구분, 동일시간틱건수, 체결강도, 연중최고가, 연중최저가, 연중최고거래량, 상장최고거래량, 연중최저거래량, 상장최저거래량, 상장중최고가, 상장중최저가, 52주최고가, 52주최저가, 52주최고거래량, 52주최저거래량, 전일외국인자료일자, 외국인한도주식수, 외국인주문가능주식수, 외국인한도비율, 외국인보유주식수, 장개시전시간외종가, 시간전전체거래량, 장중대량거래량, 장종료후시간외종가 거래량, 장종료후시간외종가 대량거래량, 시장구분, 전일종가, 전일거래량. 주요 내용: 이 테이블은 산업별 종목 코드를 매핑하며, 주가의 시가, 고가, 저가, 연중 최고가 등의 정보 및 외국인 보유 관련 정보를 찾을 수 있습니다."
            },
            {
                "type_name": "증권종목정보_유가증권주식",
                "query": """
CREATE TABLE m_asset.securities_stock_info_kospi (
    data_date DATE,                                 -- 데이터일자
    business_date DATE,                             -- 영업일자
    stock_code VARCHAR(20),                         -- 종목코드
    governance_excellence_flag CHAR(1),             -- 지배구조우량여부
    small_business_flag CHAR(1),                    -- 중소기업여부
    issue_price BIGINT,                             -- 발행가격    
    PRIMARY KEY (stock_code, data_date),
    FOREIGN KEY(stock_code, data_date) REFERENCES m_asset.exchange_kosdaq_stock_master(stock_code, data_date),
    FOREIGN KEY(stock_code, data_date) REFERENCES m_asset.exchange_kosdaq_stock_master_01(stock_code, data_date)
);
                """,
                "explanation": "유가증권, 코스피, 지배구조우량여부, 중소기업여부, 발행가격",
                "search_content": "테이블 이름: 증권종목정보_유가증권주식. 설명: 유가증권, 코스피, 지배구조우량여부, 중소기업여부, 발행가격. 주요 내용: 이 테이블은 산업별 코스피 종목 코드를 매핑하며, 지배구조우량여부, 중소기업여부, 발행가격 정보를 찾을 수 있습니다."
            },
            {
                "type_name": "증권종목정보_코스닥주식",
                "query": """
CREATE TABLE m_asset.securities_stock_info_kosdaq (
    data_date DATE,                                 -- 데이터일자
    business_date DATE,                             -- 영업일자
    stock_code VARCHAR(20),                         -- 종목코드
    governance_excellence_flag CHAR(1),             -- 지배구조우량여부
    small_business_flag CHAR(1),                    -- 중소기업여부
    issue_price BIGINT,                             -- 발행가격    
    PRIMARY KEY (stock_code, data_date),
    FOREIGN KEY(stock_code, data_date) REFERENCES m_asset.exchange_kosdaq_stock_master(stock_code, data_date),
    FOREIGN KEY(stock_code, data_date) REFERENCES m_asset.exchange_kosdaq_stock_master_01(stock_code, data_date)
);
                """,
                "explanation": "코스닥, 지배구조우량여부, 중소기업여부, 발행가격",
                "search_content": "테이블 이름: 증권종목정보_코스닥주식. 설명: 코스닥, 지배구조우량여부, 중소기업여부, 발행가격. 주요 내용: 이 테이블은 산업별 코스닥 종목 코드를 매핑하며, 지배구조우량여부, 중소기업여부, 발행가격 정보를 찾을 수 있습니다."
            },
            {
                "type_name": "일별_체결_자료",
                "query": """
CREATE TABLE m_asset.daily_trade_execution_data (
    data_date DATE,                    -- 자료일자
    stock_code VARCHAR(20),            -- 종목코드
    process_time VARCHAR(10),          -- 자료처리시간
    close_price BIGINT,                -- 종가
    prev_comparison_type VARCHAR(10),  -- 전일대비구분
    prev_comparison_amount BIGINT,     -- 전일대비금액
    trading_volume BIGINT,             -- 거래량
    trading_amount BIGINT,             -- 거래대금
    unit_trading_volume BIGINT,        -- 단위거래량
    unit_trading_amount BIGINT,        -- 단위거래대금
    open_price BIGINT,                 -- 시가
    high_price BIGINT,                 -- 고가
    low_price BIGINT,                  -- 저가
    ask_price BIGINT,                  -- 매도호가
    bid_price BIGINT,                  -- 매수호가
    execution_type_code VARCHAR(10),   -- 체결유형코드
    market_trade_type VARCHAR(10),     -- 시장매매구분
    market_time_type VARCHAR(10),      -- 시장시간구분
    market_transaction_type VARCHAR(10), -- 시장거래구분
    ask_bid_execution_type VARCHAR(10), -- 매도매수체결구분
    ask_trading_volume BIGINT,         -- 매도거래량
    bid_trading_volume BIGINT,         -- 매수거래량
    execution_strength_type VARCHAR(10), -- 체결강도구분
    PRIMARY KEY (data_date, stock_code, process_time),
    FOREIGN KEY(stock_code, data_date) REFERENCES m_asset.exchange_kosdaq_stock_master(stock_code, data_date),
    FOREIGN KEY(stock_code, data_date) REFERENCES m_asset.exchange_kosdaq_stock_master_01(stock_code, data_date)
);
                """,
                "explanation": "과거 시세, 일별",
                "search_content": "테이블 이름: 일별_체결_자료. 설명: 과거 시세, 일별. 주요 내용: 이 테이블은 종목 코드를 매핑하며, 과거 일별 시세 정보를 찾을 수 있습니다."
            },
            {
                "type_name": "매매_현황",
                "query": """
CREATE TABLE m_asset.trade_status (
    data_date DATE,                  -- 자료일자
    stock_code VARCHAR(20),          -- 종목코드
    investor_type_code VARCHAR(10),  -- 투자자구분코드
    sell_volume BIGINT,              -- 매도거래량
    sell_contract_amount BIGINT,     -- 매도약정금액
    buy_volume BIGINT,               -- 매수거래량
    buy_contract_amount BIGINT,       -- 매수약정금액
    PRIMARY KEY (data_date, stock_code),
    FOREIGN KEY(stock_code, data_date) REFERENCES m_asset.exchange_kosdaq_stock_master(stock_code, data_date),
    FOREIGN KEY(stock_code, data_date) REFERENCES m_asset.exchange_kosdaq_stock_master_01(stock_code, data_date)    
);
                """,
                "explanation": "과거 매매 현황, 거래량",
                "search_content": "테이블 이름: 매매_현황. 설명: 과거 매매 현황, 거래량. 주요 내용: 이 테이블은 종목 코드를 매핑하며, 과거 일별 거래량 정보를 찾을 수 있습니다."
            },
            {
                "type_name": "KOSPI_체결, 당일 시세 (실시간)",
                "query": """
CREATE TABLE m_asset.kospi_trade_execution (
    data_date DATE,                        -- 데이터일자
    stock_code VARCHAR(20),                -- 종목코드
    trade_process_time TIMESTAMP,          -- 매매처리시각
    prev_comparison_price BIGINT,          -- 전일대비가격
    execution_price BIGINT,                -- 체결가격
    trade_volume BIGINT,                   -- 거래량
    open_price BIGINT,                     -- 시가
    high_price BIGINT,                     -- 고가
    low_price BIGINT,                      -- 저가
    accumulated_trade_volume BIGINT,       -- 누적거래량
    accumulated_trade_amount BIGINT,       -- 누적거래대금
    final_ask_bid_type_code VARCHAR(10),   -- 최종매도매수구분코드
    best_ask_price BIGINT,                 -- 매도최우선호가가격
    best_bid_price BIGINT,                 -- 매수최우선호가가격
    PRIMARY KEY (data_date, stock_code, trade_process_time),
    FOREIGN KEY(stock_code, data_date) REFERENCES m_asset.exchange_kosdaq_stock_master(stock_code, data_date),
    FOREIGN KEY(stock_code, data_date) REFERENCES m_asset.exchange_kosdaq_stock_master_01(stock_code, data_date)   
);
                """,
                "explanation": "코스피 실시간",
                "search_content": "테이블 이름: KOSPI_체결, 당일 시세 (실시간). 설명: 코스피 실시간. 주요 내용: 이 테이블은 종목 코드를 매핑하며, 코스피 종목의 실시간 시세 정보를 찾을 수 있습니다."
            },
            {
                "type_name": "KOSDAQ_체결, 당일 시세 (실시간)",
                "query": """
CREATE TABLE m_asset.kosdaq_trade_execution (
    data_date DATE,                        -- 데이터일자
    stock_code VARCHAR(20),                -- 종목코드
    trade_process_time TIMESTAMP,          -- 매매처리시각
    prev_comparison_price BIGINT,          -- 전일대비가격
    execution_price BIGINT,                -- 체결가격
    trade_volume BIGINT,                   -- 거래량
    open_price BIGINT,                     -- 시가
    high_price BIGINT,                     -- 고가
    low_price BIGINT,                      -- 저가
    accumulated_trade_volume BIGINT,       -- 누적거래량
    accumulated_trade_amount BIGINT,       -- 누적거래대금
    final_ask_bid_type_code VARCHAR(10),   -- 최종매도매수구분코드
    best_ask_price BIGINT,                 -- 매도최우선호가가격
    best_bid_price BIGINT,                 -- 매수최우선호가가격
    PRIMARY KEY (data_date, stock_code, trade_process_time),
    FOREIGN KEY(stock_code, data_date) REFERENCES m_asset.exchange_kosdaq_stock_master(stock_code, data_date),
    FOREIGN KEY(stock_code, data_date) REFERENCES m_asset.exchange_kosdaq_stock_master_01(stock_code, data_date)   
);
                """,
                "explanation": "코스닥 실시간",
                "search_content": "테이블 이름: KOSDAQ_체결, 당일 시세 (실시간). 설명: 코스닥 실시간. 주요 내용: 이 테이블은 종목 코드를 매핑하며, 코스닥 종목의 실시간 시세 정보를 찾을 수 있습니다."
            }
        ]
    
    def setup_complete_schema_collection(self, collection_name: str = None) -> bool:
        """스키마 컬렉션 완전 설정 (생성 + 데이터 삽입)"""
        collection_name = collection_name or config.weaviate.schema_collection
        
        try:
            # 컬렉션 생성
            if not self.create_schema_collection(collection_name):
                return False
            
            # 데이터 삽입
            if not self.insert_table_schema_data(collection_name):
                return False
            
            logger.info(f"Complete schema collection setup finished: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error in complete schema collection setup: {e}")
            return False
    
    def close(self):
        """Weaviate 클라이언트 연결 종료"""
        if self._client:
            self._client.close()
            logger.info("Weaviate setup connection closed")


# 전역 설정 인스턴스
weaviate_setup = WeaviateSetup()