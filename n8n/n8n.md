# npm을 이용한 로컬 환경 구축
1. n8n 설치
```
npm install n8n -g
n8n    
```
2. (http://localhost:5678/) 구동    


# docker를 통한 n8n 설치
- https://dt-simulation.tistory.com/55 참조 
- docker-compose.yml 파일 수정 필요.


nineposes@titan-rtx:/data/bnh/n8n$ docker-compose down
nineposes@titan-rtx:/data/bnh/n8n$ docker-compose up -d



## Success!! google인증부터 GOCSPX-XXXXXXXXXXXX-unp7Bb0x-A
- 승인된 리디렉션 URI : http://localhost:5678/rest/oauth2-credential/callback
### C:\Users\interroid>ssh -L 5678:localhost:5678 nineposes@192.168.1.206
- 
- https://console.developers.google.com/apis/api/drive.googleapis.com/overview?project=1015512647269

## [OK!n8n-실전1] - 매일 아침 달러 환율, 구글 시트에 자동 기록하기 (무료 API) 
- [n8n] 구글 연동의 첫 관문! Google Credential (OAuth) 설정 완벽 가이드
- https://dt-simulation.tistory.com/56
지금 보시는 메뉴 구성이 예전 블로그 글의 스크린샷이랑 달라서 헷갈리시는 거고, 요즘 버전 n8n에서는 별도 “Settings → Credentials” 메뉴가 아니라 워크플로우 화면/Overview에서 Credential을 생성하도록 UI가 바뀌었습니다.
https://console.cloud.google.com/auth/clients?authuser=0&project=poetic-archway-424721-s4
https://console.cloud.google.com/auth/clients?project=poetic-archway-424721-s4
- 설정된 서비스 확인
https://console.cloud.google.com/apis/dashboard?authuser=0&project=poetic-archway-424721-s4

1. Credentials 화면 여는 위치 (새 UI 기준)
아래 둘 중 편한 쪽으로 하시면 됩니다.
왼쪽 사이드바에서 여는 방법
왼쪽 상단의 “햄버거”/메인 메뉴 버튼 클릭
메뉴 안에 Credentials 항목이 있습니다 → 클릭하면 My credentials 목록 화면으로 이동

- https://dt-simulation.tistory.com/57



## [n8n-실전2] - 환율 떨어지면 알림! 텔레그램 알림 봇 만들기 
- https://dt-simulation.tistory.com/63

## [OK!n8n-실전3] - RSS 를 이용한 뉴스 수집 및 텔레그램 전송
- https://dt-simulation.tistory.com/66
### -> slack로 구현 -> https를 요구해서 discord로 해보기 -> 안함. https를 요구
- slack 연동 : https://cord-ai.tistory.com/204 
    Client ID   5153536637479.10669915253957
### discord로 연동
 - https://n8n-docs.infograb.net/integrations/builtin/credentials/discord/
 - 웹후크 URL : https://discord.com/api/webhooks/1481106460539XXXXXXXXXXXXXXXXXXXXXXXX
#### 1단계: Discord Developer Portal 설정
 1. Discord Developer Portal에 접속하여 New Application을 만듭니다.
 2. 왼쪽 메뉴 Bot 클릭 -> Reset Token을 눌러 토큰을 생성하고 복사해 둡니다. (이게 n8n에 들어갈 비밀번호입니다.)
    MTQ4MTEwNzEyMjM5NjU5ODQyNg.GYMXXXXXXXXXXXXXXXXXXXXXXXXXXXX
 3. 아래쪽 Privileged Gateway Intents 섹션에서 Presence Intent, Server Members Intent, Message Content Intent를 모두 활성화(On)하고 저장합니다.
#### 2단계: 서버에 봇 초대하기
 1. 왼쪽 메뉴 OAuth2 -> URL Generator 클릭.
 2. Scopes에서 bot, Administrator(또는 필요한 권한) 체크.
 3. 하단에 생성된 URL을 복사해 브라우저 주소창에 넣고, 내 서버를 선택해 봇을 초대합니다.
 https://discord.com/oauth2/authorize?client_id=14811071223XXXXXXXXX&permissions=8&integration_type=0&scope=bot
#### 3단계: n8n 연동
 1. n8n에서 Discord 노드 추가 -> Credential에서 Create New 선택.
 2. Authentication 방식을 Bot Token으로 선택합니다.
 3. 복사해둔 Bot Token을 붙여넣고 저장합니다. 

    실전 운영 환경에서는 '데이터 중복(Data Redundancy)' 문제를 반드시 해결하는 방법을 공부해봅시다.
    RSS 피드는 보통 최근 10~20개의 기사를 계속 보여줍니다. 만약 1시간마다 봇을 실행하면, 이미 봤던 기사가 또 수집되고 알림이 갈 수 있습니다.
    포스팅에서는 n8n의 Date & Time 로직을 활용하여 "직전 실행 이후에 발행된 최신 뉴스"만 정확히 필터링하고, 이를 구글 시트에 아카이빙한 후 텔레그램으로 브리핑하는 무결성 높은 데이터 파이프라인을 구축
- https://www.gpters.org/nocode/post/gmail-interlocking-n8n-cloud-9XBb19CsIwBrmI5
    * n8n & Gmail API 연동

## [OK!n8n-실전4] - 개발자의 주식 치트키: DeepSeek & RSS.app으로 'AI 여의도 애널리스트' 만들기
- https://dt-simulation.tistory.com/70



## [OK!n8n-실전5] - 쏟아지는 업무 메일, AI가 3줄 요약해서 텔레그램으로 쏴준다! (Gmail + DeepSeek)
- https://dt-simulation.tistory.com/74


## n8n docker backup

### 방법 1: Docker 볼륨 통째로 백업 (가장 추천)
1. 안전한 백업을 위해 잠시 컨테이너 중지
docker-compose stop

2. 볼륨 데이터를 현재 폴더에 n8n_full_backup.tar로 압축
docker run --rm -v n8n_data:/source -v $(pwd):/backup busybox tar cvf /backup/n8n_full_backup.tar -C /source .

3. 컨테이너 다시 시작
docker-compose start

### 방법 2: n8n CLI를 이용한 JSON 추출 (이식성 좋음)
데이터베이스 파일이 아닌, 읽기 가능한 JSON 파일 형태로 워크플로우와 자격 증명을 따로 뽑아내는 방법입니다. 다른 n8n 서버로 옮길 때 매우 유용합니다.

1. 워크플로우 전체 내보내기
docker exec -it bnh_poc_n8n n8n export:workflow --all --output=/data/bnh/n8n/.n8n/workflows_export.json

2. 자격 증명(Credentials) 전체 내보내기
docker exec -it bnh_poc_n8n n8n export:credentials --all --output=/data/bnh/n8n/.n8n/creds_export.json
결과 확인: 실행 후 볼륨 폴더(또는 컨테이너 내부)에 workflows_export.json과 creds_export.json 파일이 생성됩니다.