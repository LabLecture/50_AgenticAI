# supp_08 실습 코드 — 백엔드를 브라우저로 (React 챗 프론트 + 풀스택 연동)

보충 교안 8(`../supp_08_react_frontend_fullstack.md`)의 정답/참고 코드.
day13·day14 백엔드를 한 파일로 통합한 `backend/`, React 챗 `frontend/`, 그리고 6교시용 `nginx.conf`·`docker-compose.yml` 로 구성된다.

```
supp_08/
├── backend/
│   ├── server.py          # CORS + /chat + /chat/stream + /chat/sse + /ws/chat (MLAPI)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── package.json
│   ├── public/index.html
│   ├── .env.development   # REACT_APP_API_URL
│   ├── Dockerfile
│   └── src/
│       ├── index.js
│       ├── App.js                  # 3개 모드 탭 전환
│       └── components/
│           ├── Chat.js             # 2교시 · axios 비스트리밍
│           ├── ChatStream.js       # 4교시 · fetch+getReader 스트리밍
│           └── ChatWs.js           # 5교시 · WebSocket
├── nginx.conf             # 6교시(이론) 리버스 프록시 예시
└── docker-compose.yml     # 6교시 통합 기동
```

## 키 (MLAPI)

day11~15 와 동일하게 **repo 루트 `.env`** 의 `MLAPI_*` 를 사용한다(새 키 불필요).
```
MLAPI_BASE_URL=https://mlapi.run/.../v1
MLAPI_API_KEY=...
MLAPI_MODEL=openai/gpt-4o-mini
```

## 실행 (로컬 2-프로세스)

**1) 백엔드** (yeardream 환경 — fastapi/uvicorn/openai 이미 설치됨)
```powershell
cd supp/supp_08/backend
uvicorn server:app --reload --port 8000
# 확인: http://localhost:8000/health , http://localhost:8000/docs
```

**2) 프론트엔드** (Node 18+)
```powershell
cd supp/supp_08/frontend
npm install
npm start        # http://localhost:3000
```
상단 탭으로 **비스트리밍 / 스트리밍 / WebSocket** 세 방식을 전환하며 비교한다.

> 2교시처럼 백엔드에 CORS 가 없으면 브라우저 콘솔에 CORS 에러가 뜬다. `server.py` 의 `CORSMiddleware` 가 그걸 해소한다(3교시).

## 실행 (docker-compose · 6교시)
```powershell
cd supp/supp_08
docker-compose up --build      # backend:8000 + frontend:3000
```

## 엔드포인트 요약

| 메서드 | 경로 | 교시 | 설명 |
|--------|------|------|------|
| GET | `/health` | - | 상태 확인 |
| POST | `/chat` | 2 | 비스트리밍 → `{"reply": "..."}` |
| POST | `/chat/stream` | 4 | `text/plain` 토큰 스트림 (+ `\n[DONE]`) |
| POST | `/chat/sse` | 4 | `text/event-stream` (`data: ...`) |
| WS | `/ws/chat` | 5 | 양방향 실시간 챗 |

## 검증 상태

백엔드는 yeardream 환경에서 실제 MLAPI 키로 검증 완료:
CORS preflight(`Access-Control-Allow-Origin`), `/chat`, `/chat/stream`(`X-Accel-Buffering:no`+`[DONE]`), `/chat/sse`(`data:`), `/ws/chat` 모두 정상.
프론트엔드는 표준 CRA 구조이며 `npm install` 후 동작한다.
