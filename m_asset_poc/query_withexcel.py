import pandas as pd
import re
from langchain_core.messages import HumanMessage, AIMessage
from datetime import datetime
import os
import asyncio
from typing import Dict, List, Optional, Any
import aiofiles
from pathlib import Path
import sys

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agents.text_to_sql_agent import text_to_sql_agent
from src.core.concurrency_limiter import ConcurrencyLimiter

# Excel 처리 전용 동시성 제한기 (더 적은 수로 설정)
excel_concurrency_limiter = ConcurrencyLimiter(
    max_concurrent=int(os.getenv("EXCEL_MAX_CONCURRENT_QUERIES", "5")),
    timeout=float(os.getenv("EXCEL_QUERY_TIMEOUT", "300"))
)


def extract_sql_syntax_check(messages):
    """
    메시지 리스트에서 'SQL query syntax check' 결과를 추출
    """
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and 'SQL query syntax check' in msg.content:
            # 'SQL query syntax check: ' 다음의 내용을 추출
            content = msg.content
            if 'SQL query syntax check:' in content:
                result = content.split('SQL query syntax check:')[1].strip()
                # 첫 번째 줄만 가져오기 (PASSED, FAILED 등)
                first_line = result.split('\n')[0].strip()
                return first_line
    return 'N/A'


def check_query_result_status(query_result):
    """
    query_result가 있으면 'O', 없거나 빈 값이면 'N' 반환
    """
    if query_result and str(query_result).strip() and str(query_result).strip() != '':
        return 'O'
    else:
        return 'N'


async def process_single_query_async(query: str, text_to_sql_app, row_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    단일 쿼리를 비동기로 처리하고 결과를 반환
    
    Args:
        query: 처리할 쿼리
        text_to_sql_app: Text2SQL 애플리케이션 객체
        row_info: 행 정보 (NO, index 등)
    """
    no = row_info['NO']
    index = row_info['index']
    
    try:
        # 동시성 제한기를 통해 실행
        async with excel_concurrency_limiter.acquire(request_id=f"excel_query_{no}") as request_info:
            wait_time = request_info.get("wait_time", 0.0) if request_info else 0.0
            
            if wait_time > 0:
                print(f"  [NO: {no}] 대기 시간: {wait_time:.2f}초")
            
            print(f"  [NO: {no}] 처리 시작: {query[:50]}...")
            
            # Text2SQL 에이전트 실행 (동기 함수를 비동기로 실행)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                text_to_sql_app.query,
                query
            )
            
            # 결과에서 필요한 정보 추출
            final_query = result.get('final_query', '')
            query_result = result.get('query_result', '')
            messages = result.get('messages', [])
            
            # SQL syntax check 결과 추출
            syntax_check = extract_sql_syntax_check(messages)
            
            # 결과 상태 확인
            result_status = check_query_result_status(query_result)
            
            print(f"  [NO: {no}] 완료 - 구문O: {syntax_check}, 결과O: {result_status}")
            
            return {
                'index': index,
                'NO': no,
                'final_query': final_query,
                'syntax_check': syntax_check,
                'result_status': result_status,
                'error': None
            }
            
    except asyncio.TimeoutError:
        error_msg = "쿼리 처리 시간 초과"
        print(f"  [NO: {no}] 타임아웃: {error_msg}")
        return {
            'index': index,
            'NO': no,
            'final_query': '',
            'syntax_check': f'TIMEOUT: {error_msg}',
            'result_status': 'N',
            'error': error_msg
        }
    except Exception as e:
        error_msg = str(e)
        print(f"  [NO: {no}] 오류: {error_msg}")
        return {
            'index': index,
            'NO': no,
            'final_query': '',
            'syntax_check': f'ERROR: {error_msg}',
            'result_status': 'N',
            'error': error_msg
        }


def create_example_excel(output_path="example_queries.xlsx"):
    """
    예제 Excel 파일 생성
    
    Args:
        output_path: 출력 Excel 파일 경로
    """
    import pandas as pd
    
    # 예제 데이터
    example_data = {
        'NO': [1, 2, 3, 4, 5],
        '질의': [
            '시가총액 상위 10개 회사를 알려주세요',
            '삼성전자의 현재 주가를 알려주세요',
            '최근 일주일간 거래량이 가장 많은 종목은?',
            'KOSPI 지수 상위 5개 종목의 정보를 보여주세요',
            '전일 대비 상승률이 가장 높은 종목을 찾아주세요'
        ],
        '구문': ['', '', '', '', ''],
        '구문O': ['', '', '', '', ''],
        '결과O': ['', '', '', '', '']
    }
    
    df = pd.DataFrame(example_data)
    df.to_excel(output_path, index=False)
    print(f"예제 Excel 파일이 생성되었습니다: {output_path}")
    return output_path


async def save_intermediate_results(df: pd.DataFrame, output_file_path: str, message: str = ""):
    """
    중간 결과를 비동기로 저장
    """
    try:
        # pandas의 to_excel은 동기 작업이므로 스레드 풀에서 실행
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, df.to_excel, output_file_path, False)
        
        if message:
            print(f"  {message}: {output_file_path}")
    except Exception as e:
        print(f"  파일 저장 오류: {str(e)}")


async def process_excel_batch_async(excel_file_path: str, text_to_sql_app, output_file_path: Optional[str] = None, save_interval: int = 10):
    """
    엑셀 파일을 읽어서 비동기로 일괄 처리하고 결과를 저장
    
    Args:
        excel_file_path: 입력 엑셀 파일 경로
        text_to_sql_app: Text2SQL 애플리케이션 객체
        output_file_path: 출력 엑셀 파일 경로 (None이면 자동 생성)
        save_interval: 중간 저장 간격
    """
    
    # 엑셀 파일 읽기
    try:
        df = pd.read_excel(excel_file_path)
        print(f"엑셀 파일 로드 완료: {len(df)} rows")
    except Exception as e:
        print(f"엑셀 파일 읽기 오류: {str(e)}")
        return
    
    # 필요한 컬럼 확인
    required_columns = ['NO', '질의']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"필수 컬럼이 없습니다: {missing_columns}")
        return
    
    # 결과 컬럼이 없으면 추가
    result_columns = ['구문', '구문O', '결과O']
    for col in result_columns:
        if col not in df.columns:
            df[col] = ''
    
    # 처리할 작업 목록 생성
    tasks = []
    total_rows = len(df)
    
    for index, row in df.iterrows():
        no = row['NO']
        query = row['질의']
        
        # 질의가 비어있으면 스킵
        if pd.isna(query) or str(query).strip() == '':
            print(f"[{index+1}/{total_rows}] NO: {no} - 질의가 비어있음 (스킵)")
            continue
        
        # 비동기 작업 추가
        task_info = {
            'index': index,
            'NO': no,
            'query': str(query)
        }
        tasks.append(process_single_query_async(str(query), text_to_sql_app, task_info))
    
    if not tasks:
        print("처리할 쿼리가 없습니다.")
        return
    
    print(f"\n총 {len(tasks)}개의 쿼리를 비동기로 처리합니다.")
    print(f"최대 동시 처리 수: {excel_concurrency_limiter.max_concurrent}")
    print("-" * 50)
    
    # 비동기 작업 실행
    start_time = datetime.now()
    completed_count = 0
    error_count = 0
    
    # 작업을 배치로 나누어 처리 (메모리 효율성을 위해)
    batch_size = save_interval
    for i in range(0, len(tasks), batch_size):
        batch_tasks = tasks[i:i+batch_size]
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # 결과를 데이터프레임에 저장
        for result in batch_results:
            if isinstance(result, Exception):
                print(f"처리 중 예외 발생: {result}")
                error_count += 1
            else:
                index = result['index']
                df.at[index, '구문'] = result['final_query']
                df.at[index, '구문O'] = result['syntax_check']
                df.at[index, '결과O'] = result['result_status']
                
                if result['error']:
                    error_count += 1
                completed_count += 1
        
        # 중간 저장
        if (i + batch_size) < len(tasks):  # 마지막 배치가 아닌 경우에만
            temp_output = output_file_path or f"temp_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            await save_intermediate_results(df, temp_output, f"중간 저장 완료 ({completed_count}/{len(tasks)})")
    
    # 최종 결과 저장
    if output_file_path is None:
        output_file_path = f"text2sql_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    try:
        await save_intermediate_results(df, output_file_path)
        
        elapsed_time = (datetime.now() - start_time).total_seconds()
        print(f"\n처리 완료!")
        print(f"총 처리 시간: {elapsed_time:.2f}초")
        print(f"평균 처리 시간: {elapsed_time/len(tasks):.2f}초/쿼리")
        print(f"총 처리된 질의: {completed_count}/{total_rows}")
        print(f"오류 발생: {error_count}")
        print(f"결과 파일: {output_file_path}")
        
        # 동시성 통계
        concurrency_stats = excel_concurrency_limiter.get_status()
        print(f"\n=== 동시성 처리 통계 ===")
        print(f"총 처리 요청: {concurrency_stats['total_processed']}")
        print(f"평균 대기 시간: {concurrency_stats['average_wait_time']:.2f}초")
        
        # 통계 출력
        syntax_passed = len(df[df['구문O'].str.contains('PASSED', na=False)])
        syntax_failed = len(df[df['구문O'].str.contains('FAILED', na=False)])
        result_success = len(df[df['결과O'] == 'O'])
        result_fail = len(df[df['결과O'] == 'N'])
        
        print(f"\n=== 처리 결과 통계 ===")
        print(f"구문 체크 성공: {syntax_passed}")
        print(f"구문 체크 실패: {syntax_failed}")
        print(f"쿼리 실행 성공: {result_success}")
        print(f"쿼리 실행 실패: {result_fail}")
        
    except Exception as e:
        print(f"결과 파일 저장 오류: {str(e)}")


# 동기 함수 래퍼 (기존 코드와의 호환성을 위해)
def process_excel_batch(excel_file_path: str, text_to_sql_app, output_file_path: Optional[str] = None):
    """
    기존 동기 함수와의 호환성을 위한 래퍼
    """
    asyncio.run(process_excel_batch_async(excel_file_path, text_to_sql_app, output_file_path))


async def main_async():
    """Excel 배치 처리 비동기 메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Excel 파일의 자연어 질의를 비동기로 일괄 처리하여 SQL 변환 및 실행",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예제:
  python query_withexcel.py input.xlsx
  python query_withexcel.py input.xlsx --output results.xlsx
  python query_withexcel.py queries.xlsx --output batch_results.xlsx --interval 5
  python query_withexcel.py queries.xlsx --concurrent 3

Excel 파일 형식:
  필수 컬럼: NO, 질의
  결과 컬럼: 구문 (생성된 SQL), 구문O (구문 체크 결과), 결과O (실행 성공 여부)

환경 변수:
  EXCEL_MAX_CONCURRENT_QUERIES: 최대 동시 처리 쿼리 수 (기본값: 5)
  EXCEL_QUERY_TIMEOUT: 쿼리 타임아웃 (초, 기본값: 300)
        """
    )
    
    parser.add_argument("input", nargs='?', help="입력 Excel 파일 경로 (NO, 질의 컬럼 필수)")
    parser.add_argument("--output", "-o", help="출력 Excel 파일 경로 (기본값: 자동 생성)")
    parser.add_argument("--interval", "-i", type=int, default=10, 
                       help="중간 저장 간격 (기본값: 10)")
    parser.add_argument("--concurrent", "-c", type=int, 
                       help="최대 동시 처리 수 (환경 변수 EXCEL_MAX_CONCURRENT_QUERIES 덮어쓰기)")
    parser.add_argument("--create-example", action="store_true", 
                       help="예제 Excel 파일 생성")
    
    args = parser.parse_args()
    
    # 예제 파일 생성 모드
    if args.create_example:
        output_path = args.output if args.output else "example_queries.xlsx"
        create_example_excel(output_path)
        return
    
    # 동시 처리 수 설정
    if args.concurrent:
        excel_concurrency_limiter.max_concurrent = args.concurrent
        print(f"⚙️  최대 동시 처리 수를 {args.concurrent}로 설정했습니다.")
    
    # 입력 파일 존재 확인
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 입력 파일을 찾을 수 없습니다: {input_path}")
        sys.exit(1)
    
    if not input_path.suffix.lower() in ['.xlsx', '.xls']:
        print(f"❌ Excel 파일이 아닙니다: {input_path}")
        sys.exit(1)
    
    print(f"📁 입력 파일: {input_path}")
    if args.output:
        print(f"📁 출력 파일: {args.output}")
    print(f"💾 중간 저장 간격: {args.interval}개")
    print(f"⚡ 최대 동시 처리: {excel_concurrency_limiter.max_concurrent}개")
    print("-" * 50)
    
    try:
        # 에이전트 가져오기
        agent = text_to_sql_agent
        if not agent:
            print("❌ Text-to-SQL 에이전트를 초기화할 수 없습니다.")
            sys.exit(1)
        
        # Excel 배치 처리 실행
        await process_excel_batch_async(
            excel_file_path=str(input_path),
            text_to_sql_app=agent,
            output_file_path=args.output,
            save_interval=args.interval
        )
        
    except KeyboardInterrupt:
        print("\n⚠️  사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # 이벤트 루프 실행
    asyncio.run(main_async())