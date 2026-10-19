import os

# 스키마는 .env 의 DB_SCHEMA (기본 public, insert.sql 기준). 기존 운영 DB 는 graywhale
DB_SCHEMA = os.getenv("DB_SCHEMA", "public")

select_test = f"""
    SELECT * FROM {DB_SCHEMA}.wj_members
    WHERE user_name = %s
"""

select_class_info = f"""
    SELECT * FROM {DB_SCHEMA}.wj_members wjm
    INNER JOIN {DB_SCHEMA}.wj_members_progress wjmp on wjm.user_id = wjmp.user_id
    WHERE user_name = %s 
    and user_school = %s 
    and user_grade = %s
"""

select_class_progress_info = f"""
    SELECT * FROM {DB_SCHEMA}.wj_members wjm
    INNER JOIN {DB_SCHEMA}.wj_members_progress wjmp on wjm.user_id = wjmp.user_id
    WHERE user_name = %s 
    and user_school = %s 
    and user_grade = %s
"""

select_class_progress_info_02 = f"""
    SELECT * FROM {DB_SCHEMA}.wj_members wjm
    INNER JOIN {DB_SCHEMA}.wj_members_progress wjmp on wjm.user_id = wjmp.user_id
    WHERE wjm.user_name = %s
    and (subject_name like %s or (subject_id = %s and subject_id != '0') )
"""