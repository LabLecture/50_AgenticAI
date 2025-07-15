import logging
from typing import Annotated

from langchain_core.tools import tool

from src.tools.db import PostgreSqlDB
from src.tools import db_sql

logger = logging.getLogger(__name__)
postrgre_db = PostgreSqlDB()


@tool
def link_provider_tool(
    user_name: Annotated[str, "학생(자녀)이름, default value is **샘플스**"],
    class_data: Annotated[str, "수업이름, default value is **샘플**"],
    class_id: Annotated[str, "수업번호, default value is **0**"]
) -> str:
    """학생(자녀)의 **수업 상세정보 링크**를 제공합니다. 이 도구는 수업의 진도가 아닌, 웹 페이지 주소(URL)를 제공할 때 사용됩니다.
       추가적인 지시사항: 
       - "'수업이름' ....", "'수업번호'. '수업이름' 수업 ....", "'수업번호' ....", 과 같은 형식의 질문을 받아야합니다.("...."는 추가로 붙을 수 있는 말입니다.('이요', '입니다' 등등))
       - 위 형식외의 질문은 받으면 안됩니다.
       - "'수업이름' ...." 이 형식의 경우 수업번호는 default 값이고 수업이름은 '수업이름' 입니다.
       - "'수업번호'. '수업이름' 수업 ...." 이 형식의 경우 수업번호는 '수업번호' 이고 수업이름은 '수업이름' 입니다.
       - "'수업번호' ...." 이 형식의 경우 수업번호는 '수업번호' 이고 수업이름은 default 값입니다.
    """
    try:
        # Parameters for the request
        print(f"link_provider_tool_start_user_name: {user_name}, class_data: {class_data}, class_id: {class_id}")
        
        # 'subjectId'와 같은 링크 구성에 필요한 정보를 조회하는 SQL을 호출해야 합니다.
        # link_data = postrgre_db.fetch_one(db_sql.select_class_progress_info_02, (user_name, f"%{class_data}%", class_id))

        if class_id is None:
            return "입력 정보에 부합되는 수업 링크 정보를 찾을 수 없습니다. 다시 입력해주세요."
            
        # 에이전트가 URL을 완성할 수 있도록 'subject_id'를 포함한 결과 반환
        # 예: {'subject_id': '0001'} 형태의 결과를 가정
        # subject_id = link_data['subject_id']
        full_url = f"https://m.kingwssmindsyc.com/prod/subjectDetail.do?subjectId={class_id}"

        return f'''
        학생(자녀)이름:{user_name}
        수업링크:{full_url}
        '''
    except BaseException as e:
        error_msg = f"Failed to get link. Error: {repr(e)}"
        logger.error(error_msg)
        return error_msg