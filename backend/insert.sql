CREATE TABLE wj_members (
  user_id VARCHAR(50) NOT NULL,
  user_name VARCHAR(100) NOT NULL,
  user_school VARCHAR(100) NOT NULL,
  user_grade INT
);

INSERT INTO wj_members ( user_id,user_name,user_school,user_grade ) values 
('1', '송혜교', '쌍문초등학교', 6), ('2', '장원영', '미아초등학교', 2);

CREATE TABLE wj_members_progress (
    user_id VARCHAR(50) NOT NULL,
    subject_id VARCHAR(50) NOT NULL,
    subject_name VARCHAR(50) NOT NULL,
    subject_last_mm VARCHAR(50) NOT NULL,
    subject_this_mm VARCHAR(50) NOT NULL
);

INSERT INTO wj_members_progress ( user_id,subject_id,subject_name,subject_last_mm,subject_this_mm ) VALUES 
('1', '1', 'AI수학 프로그램', '나눗셈/원', '분수/들이와무게 에서 [H6] 4.분수(2)'),
('1', '2', '창의STEAM 수업', 'Level 1 코딩전문가 6 함수', 'Level 2 문제해결자 9 자동화/도식화/유추'),
('1', '3', '슬기로운 생활', '4장 독서의 필요성', '3. 추천도서목록'),
('2', '3', '슬기로운 생활', '4장 독서의 필요성', '3. 추천도서목록');

