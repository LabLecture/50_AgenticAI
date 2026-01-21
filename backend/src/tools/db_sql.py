select_test = """
    SELECT * FROM graywhale.wj_members
    WHERE user_name = %s
"""

select_class_info = """
    SELECT * FROM graywhale.wj_members wjm
    INNER JOIN graywhale.wj_members_progress wjmp on wjm.user_id = wjmp.user_id
    WHERE user_name = %s 
    and user_school = %s 
    and user_grade = %s
"""

select_class_progress_info = """
    SELECT * FROM graywhale.wj_members wjm
    INNER JOIN graywhale.wj_members_progress wjmp on wjm.user_id = wjmp.user_id
    WHERE user_name = %s 
    and user_school = %s 
    and user_grade = %s
"""

select_class_progress_info_02 = """
    SELECT * FROM graywhale.wj_members wjm
    INNER JOIN graywhale.wj_members_progress wjmp on wjm.user_id = wjmp.user_id
    WHERE wjm.user_name = %s
    and (subject_name like %s or (subject_id = %s and subject_id != '0') )
"""