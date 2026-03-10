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

## [n8n] 실전 (1) - 매일 아침 달러 환율, 구글 시트에 자동 기록하기 (무료 API)
- https://dt-simulation.tistory.com/57
- [n8n] 구글 연동의 첫 관문! Google Credential (OAuth) 설정 완벽 가이드
- https://dt-simulation.tistory.com/56


## [n8n] 실전 (2) - 환율 떨어지면 알림! 텔레그램 알림 봇 만들기
- https://dt-simulation.tistory.com/63

## [n8n] 실전 (3) - RSS 를 이용한 뉴스 수집 및 텔레그램 전송
- https://dt-simulation.tistory.com/66

## [n8n] 실전 (4) - 개발자의 주식 치트키: DeepSeek & RSS.app으로 'AI 여의도 애널리스트' 만들기
- https://dt-simulation.tistory.com/70

## [n8n] 실전 (5) - 쏟아지는 업무 메일, AI가 3줄 요약해서 텔레그램으로 쏴준다! (Gmail + DeepSeek)
- https://dt-simulation.tistory.com/74
