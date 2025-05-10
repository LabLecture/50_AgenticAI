import logging
from typing import Annotated

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from .decorators import log_io

# from db import PostgreSqlDB
# import db_sql
from src.tools.db import PostgreSqlDB
from src.tools import db_sql
# from src.crawler import Crawler

logger = logging.getLogger(__name__)
postrgre_db = PostgreSqlDB()


@tool
@log_io
def class_progress_tool(
    user_name:Annotated[str, "학생(자녀)이름, default value is **샘플스**"],
    class_data:Annotated[str, "수업이름, default value is **샘플**"],
    class_id:Annotated[str, "수업번호, default value is **0**"]
    ) -> str:
    """학생(자녀)의 **수업진도**를 체크(조회,확인)합니다.
        추가적인 지시사항: 
        - "'수업이름' ....", "'수업번호'. '수업이름' 수업 ....", "'수업번호' ....", 과 같은 형식의 질문을 받아야합니다.("...."는 추가로 붙을 수 있는 말입니다.('이요', '입니다' 등등))
        - 위 형식외의 질문은 받으면 안됩니다.
        - "'수업이름' ...." 이 형식의 경우 수업번호는 default 값이고 수업이름은 '수업이름' 입니다.
        - "'수업번호'. '수업이름' 수업 ...." 이 형식의 경우 수업번호는 '수업번호' 이고 수업이름은 '수업이름' 입니다.
        - "'수업번호' ...." 이 형식의 경우 수업번호는 '수업번호' 이고 수업이름은 default 값입니다.
    """
    try:
        # Parameters for the request
        class_progress_data = postrgre_db.fetch_one(db_sql.select_class_progress_info_02, (user_name, f"%{class_data}%", class_id))

        if class_progress_data is None:
            return f'''
                입력 정보에 부합되는 수업정보가 없습니다.
                다시 입력해주세요.
            '''
            raise ValueError('해당 유저의 데이터가 존재하지 않습니다')
        
        return f'''
        학생(자녀)이름:{user_name}
        수업진도:{class_progress_data}
        '''
    except BaseException as e:
        error_msg = f"Failed to crawl. Error: {repr(e)}"
        logger.error(error_msg)
        return error_msg
