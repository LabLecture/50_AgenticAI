# chatbot_light


### step_4_agent branch
1. backend fastapi runing
PS D:\GITLAB\m_asset\01_chatbot_basic> cd ..
PS D:\GITLAB\m_asset> python -m venv venv
PS D:\GITLAB\m_asset> .\venv\Scripts\activate
(venv) PS D:\GITLAB\m_asset> cd .\01_chatbot_basic\backend\
(venv) PS D:\GITLAB\m_asset\01_chatbot_basic\backend> pip install -r .\requirements.txt
(venv) PS D:\GITLAB\m_asset\01_chatbot_basic\backend> fastapi run .\main.py


2. frontend react runing (with another terminal)
PS D:\GITLAB> cd .\m_asset\01_chatbot_basic\frontend\
PS D:\GITLAB\m_asset\01_chatbot_basic\frontend> npm i
#### 경우에 따라 필요할수 있음.
PS D:\GITLAB\m_asset\01_chatbot_basic\frontend> npm audit fix

PS D:\GITLAB\m_asset\01_chatbot_basic\frontend> npm start

3.아래 시나리오로 테스트 하면 됨.
고객 : 초등학교 딸 수업진도를 체크할 수 있나요?
  챗봇 : 예. 자녀분 수업진도를 체크하려고 하시는 군요? 우선 자녀분 아이디나 학교/학년/이름을 말씀해 주실 수 있나요?
  고객 : 쌍문초등학교 6학년 송혜교
  다른 사람 수업 진도 체크 하고 싶어. 
    동생 미아초등학교 2학년 장원영 진도체크도 부탁해.
  챗봇 : 네. 고객님 자녀분 쌍문초등학교 6학년 송혜교님은 1. AI수학 프로그램 과 2. 창의STEAM 수업을 듣고 계시네요. 둘 중 어느 수업 진도를 체크하고 싶으신가요? (DB)
  고객 : 1
  챗봇 : 네. 고객님 자녀분 이웅진님은 1. AI수학 프로그램을에서 지난달엔 나눗셈/원 단원을 마쳤고, 이번달엔 분수/들이와무게 에서 [H6] 4.분수(2) 진행하고 있습니다. 초등3학년 수학 학습단원은 학교 교과와 동일하게 진행되니 참고하시기 바랍니다. 
  최근 한달간 학습한 내용에 대해 AI가 분석하여 개인별 맞춤 결과를 제공하는데, 해당 페이지 링크를 제공해 드릴까요?
  고객 : 네. 
  챗봇 : 네. 해당 주소는 https://m.wjthinkbig.com/prod/subjectDetail.do?subjectId=S0000059 입니다. 혹시 로그인이 안되어 계시면 먼저 로그인을 해야 되니, 이점 양해 바랍니다. 더 필요한 사항은 있으실까요? 학습안내, 진도체크, 문항/습관 분석 등을 도와 드릴 수 있습니다.  
