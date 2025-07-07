"""
벡터 DB를 사용할 수 없을 때 사용할 기본 스키마 정보
"""

DEFAULT_SCHEMA = """
다음은 주요 테이블의 스키마 정보입니다:

1. m_asset.exchange_kosdaq_stock_master (종목 마스터 정보)
   - stock_code: VARCHAR(10) - 종목코드
   - kor_name: VARCHAR(100) - 종목명
   - kor_name_small: VARCHAR(50) - 종목명(약식)
   - market_type: VARCHAR(20) - 시장구분 (KOSPI/KOSDAQ)
   - listed_shares: BIGINT - 상장주식수
   - capital_amount: BIGINT - 자본금
   - face_value: INTEGER - 액면가
   - data_date: DATE - 데이터 기준일

2. m_asset.exchange_kosdaq_stock_master_01 (일별 주가 정보)
   - stock_code: VARCHAR(10) - 종목코드
   - data_date: DATE - 데이터 기준일
   - close_price: NUMERIC - 종가
   - prev_close_price: NUMERIC - 전일종가
   - open_price: NUMERIC - 시가
   - high_price: NUMERIC - 고가
   - low_price: NUMERIC - 저가
   - trading_volume: BIGINT - 거래량
   - trading_amount: BIGINT - 거래대금
   - market_cap: BIGINT - 시가총액
   - high_52w_price: NUMERIC - 52주 최고가
   - low_52w_price: NUMERIC - 52주 최저가
   - foreigner_holding_shares: BIGINT - 외국인보유주식수
   - foreigner_limit_ratio: NUMERIC - 외국인한도비율

3. m_asset.industry_stock_mapping (업종 매핑)
   - stock_code: VARCHAR(10) - 종목코드
   - industry_code: VARCHAR(20) - 업종코드
   - industry_name: VARCHAR(100) - 업종명
   - market_type: VARCHAR(20) - 시장구분
   - data_date: DATE - 데이터 기준일

4. m_asset.daily_trade_execution_data (일별 거래 데이터)
   - stock_code: VARCHAR(10) - 종목코드
   - data_date: DATE - 데이터 기준일
   - trade_time: TIME - 거래시각
   - trade_price: NUMERIC - 체결가격
   - trade_volume: BIGINT - 체결수량
   - accumulated_volume: BIGINT - 누적거래량
   - accumulated_amount: BIGINT - 누적거래대금

조인 관계:
- 모든 테이블은 stock_code와 data_date로 조인 가능
- 최신 데이터를 원하면 data_date를 최근 날짜로 필터링
- 종목명은 exchange_kosdaq_stock_master.kor_name_small 사용 권장
"""

def get_default_schema():
    """기본 스키마 정보 반환"""
    return DEFAULT_SCHEMA

def get_basic_schema_examples():
    """기본 스키마 예제 반환"""
    return [
        {
            "type_name": "table_schema",
            "explanation": "종목 마스터 및 일별 주가 정보",
            "search_content": DEFAULT_SCHEMA,
            "query": DEFAULT_SCHEMA
        }
    ]