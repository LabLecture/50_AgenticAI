import logging
from typing import Annotated

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
# from .decorators import log_io

# from db import PostgreSqlDB
# import db_sql
from src.tools.db import PostgreSqlDB
from src.tools import db_sql
# from src.crawler import Crawler

logger = logging.getLogger(__name__)
postrgre_db = PostgreSqlDB()


# @log_io
@tool
def user_class_tool( # default 값에 따라 받아오는 값이 달라짐 (ex) 6, 6학년 이런게 달라짐..
    user_name:Annotated[str, "학생(자녀)이름, default value is **샘플스**"],
    user_school:Annotated[str, "학교, default value is **샘플학교**"],
    user_grade:Annotated[int, "학년, default value is **7**"]
    # ) -> dict:
    ) -> str:
    """학생(자녀)의 **수업정보**를 체크(조회,확인)합니다.
        추가적인 지시사항:
        - 유저 이름이나 학교명이 구체적으로 명시되지 않은 경우(예: '제 딸', '초등학교' 등), 해당 정보는 수집하지 마십시오.
        - 구체적인 이름과 학교명이 제공된 경우에만 user_name과 user_school을 설정하십시오.
        - 일반적인 명칭이 입력된 경우 "안녕하세요 학습지 챗봇입니다. 자녀의 이름과 학교명을 구체적으로 알려주세요."라고 응답하십시오.
    """
    try:
        # Parameters for the request
        print(f"user_class_tool_start_user_name: {user_name}, user_school: {user_school}, user_grade: {user_grade}")
        class_datas = postrgre_db.fetch_all(db_sql.select_class_info, (user_name, user_school, user_grade))

        if class_datas is None:
            return "입력 정보에 부합되는 수업정보가 없습니다.  다시 자녀정보를 입력해주세요."
        
        # 수업 정보 포맷팅
        subjects = "\n".join([
            f"{i+1}. {item['subject_name']}\n"
            for i, item in enumerate(class_datas)
        ])
        return f"학생(자녀)이름:{user_name}\n학교:{user_school}\n학년:{user_grade}\n수업정보:\n{subjects}"
    except BaseException as e:
        error_msg = f"Failed to crawl. Error: {repr(e)}"
        logger.error(error_msg)
        return error_msg
