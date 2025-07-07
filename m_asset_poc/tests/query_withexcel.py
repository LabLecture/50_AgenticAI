import pandas as pd
import re
from langchain_core.messages import HumanMessage, AIMessage
from datetime import datetime
import os

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

def process_single_query(query, text_to_sql_app):
    """
    단일 쿼리를 처리하고 결과를 반환
    """
    try:
        print(f"Processing query: {query[:50]}...")
        
        # Text2SQL 앱 실행
        inputs = {"messages": [HumanMessage(content=query)]}
        result = text_to_sql_app.invoke(inputs)
        
        # 결과에서 필요한 정보 추출
        final_query = result.get('final_query', '')
        query_result = result.get('query_result', '')
        messages = result.get('messages', [])
        
        # SQL syntax check 결과 추출
        syntax_check = extract_sql_syntax_check(messages)
        
        # 결과 상태 확인
        result_status = check_query_result_status(query_result)
        
        return {
            'final_query': final_query,
            'syntax_check': syntax_check,
            'result_status': result_status,
            'error': None
        }
        
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        return {
            'final_query': '',
            'syntax_check': f'ERROR: {str(e)}',
            'result_status': 'N',
            'error': str(e)
        }

def process_excel_batch(excel_file_path, text_to_sql_app, output_file_path=None):
    """
    엑셀 파일을 읽어서 일괄 처리하고 결과를 저장
    
    Args:
        excel_file_path: 입력 엑셀 파일 경로
        text_to_sql_app: Text2SQL 애플리케이션 객체
        output_file_path: 출력 엑셀 파일 경로 (None이면 자동 생성)
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
    
    # 각 행 처리
    total_rows = len(df)
    processed_count = 0
    
    for index, row in df.iterrows():
        try:
            no = row['NO']
            query = row['질의']
            
            print(f"\n[{index+1}/{total_rows}] Processing NO: {no}")
            
            # 질의가 비어있으면 스킵
            if pd.isna(query) or str(query).strip() == '':
                print(f"  질의가 비어있음 - 스킵")
                continue
            
            # 쿼리 처리
            result = process_single_query(str(query), text_to_sql_app)
            
            # 결과를 데이터프레임에 저장
            df.at[index, '구문'] = result['final_query']
            df.at[index, '구문O'] = result['syntax_check']
            df.at[index, '결과O'] = result['result_status']
            
            processed_count += 1
            print(f"  완료 - 구문O: {result['syntax_check']}, 결과O: {result['result_status']}")
            
            # 중간 저장 (10개마다)
            if processed_count % 10 == 0:
                temp_output = output_file_path or f"temp_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                df.to_excel(temp_output, index=False)
                print(f"  중간 저장 완료: {temp_output}")
            
        except Exception as e:
            print(f"  행 처리 오류 (NO: {no}): {str(e)}")
            df.at[index, '구문'] = ''
            df.at[index, '구문O'] = f'ERROR: {str(e)}'
            df.at[index, '결과O'] = 'N'
            continue
    
    # 최종 결과 저장
    if output_file_path is None:
        output_file_path = f"text2sql_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    try:
        df.to_excel(output_file_path, index=False)
        print(f"\n처리 완료!")
        print(f"총 처리된 질의: {processed_count}/{total_rows}")
        print(f"결과 파일: {output_file_path}")
        
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

