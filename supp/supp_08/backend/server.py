"""
supp_08 풀스택 챗 백엔드 (정답 코드)

day13의 /chat + day14의 /chat/stream 을 한 파일로 통합하고,
프론트 연동에 필요한 CORS · SSE · WebSocket 을 더했다.

- LLM: MLAPI (OpenAI 호환 게이트웨이) — day11~15 와 동일. 키는 repo 루트 .env 의 MLAPI_*.
- 실행:  uvicorn server:app --reload --port 8000   (yeardream 환경)

엔드포인트
  GET  /health        살아있음 확인
  POST /chat          [2교시] 비스트리밍 → {"reply": "..."}
  POST /chat/stream   [4교시] text/plain 토큰 스트림 (+ \n[DONE] 마커)  ← fetch+getReader 로 소비
  POST /chat/sse      [4교시 변형] text/event-stream (data: ... )       ← EventSource / fetch-event-source 로 소비
  WS   /ws/chat       [5교시] 양방향 실시간 챗
"""
import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from openai import AsyncOpenAI

# 키는 repo 루트 .env 의 MLAPI_* (사용자가 루트로 이동시켜 둠).
# 이 파일 위치: supp/supp_08/backend/server.py → parents[3] 가 repo 루트.
# (주의) 상위 supp/.env 는 OpenRouter 용이라 MLAPI 키가 없음 → 루트 .env 를 명시적으로 먼저 로드.
# (도커) 컨테이너에선 /app/server.py 로 복사돼 parents[3] 가 없어 IndexError → 길이 가드로 방지.
#        도커는 compose 의 env_file(../../.env) 가 환경변수로 이미 주입돼 .env 파일이 없어도 동작.
_parents = Path(__file__).resolve().parents
if len(_parents) > 3:
    _ROOT_ENV = _parents[3] / ".env"
    if _ROOT_ENV.exists():
        load_dotenv(_ROOT_ENV)            # 로컬 실행: repo 루트 .env (MLAPI_*)
load_dotenv(find_dotenv(usecwd=True), override=False)  # 보조: 루트에 없으면 실행 위치 기준 탐색

BASE_URL = os.getenv("MLAPI_BASE_URL", "https://mlapi.run/40cc17ae-a89b-4f12-a7d6-13293180fc87/v1")
API_KEY  = os.getenv("MLAPI_API_KEY")
MODEL    = os.getenv("MLAPI_MODEL", "openai/gpt-4o-mini")

if not API_KEY:
    raise RuntimeError("MLAPI_API_KEY 가 없습니다. repo 루트 .env 를 확인하세요.")

client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)

app = FastAPI(title="supp_08 풀스택 챗 백엔드")

# ── [3교시] CORS — React(localhost:3000) 의 브라우저 요청 허용 ───────────────
# 50_AgenticAI backend/main.py [5] 와 1:1. allow_origins 에 프론트 origin 명시.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,   # 쿠키 허용
    allow_methods=["*"],      # GET/POST/OPTIONS ...
    allow_headers=["*"],      # Content-Type 등
)

# 스트리밍 응답 공통 헤더 — 프록시(nginx) 버퍼링 방지 (day14 슬72)
STREAM_HEADERS = {"X-Accel-Buffering": "no", "Cache-Control": "no-cache"}


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="사용자 질문")
    temperature: float = Field(0.3, ge=0.0, le=2.0)


@app.get("/health")
def health():
    return {"ok": True, "model": MODEL}


# ── [2교시] 비스트리밍 — day13 /chat 과 동일 계약 ──────────────────────────
@app.post("/chat")
async def chat(req: ChatRequest):
    resp = await client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": req.message}],
        temperature=req.temperature,
    )
    return {"reply": resp.choices[0].message.content}


# 공통 토큰 제너레이터 — day14 의 토큰 루프를 재사용 (가드 포함)
async def _token_stream(message: str, temperature: float = 0.3):
    stream = await client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": message}],
        temperature=temperature,
        stream=True,
    )
    async for chunk in stream:
        if not chunk.choices:
            continue
        piece = getattr(chunk.choices[0].delta, "content", None)
        if piece:
            yield piece


# ── [4교시] text/plain 청크 스트림 — 브라우저 fetch + getReader 로 소비 ───────
@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    async def gen():
        try:
            async for piece in _token_stream(req.message, req.temperature):
                yield piece
            yield "\n[DONE]"
        except Exception as e:
            yield f"\n[ERROR] {type(e).__name__}: {e}"
    return StreamingResponse(gen(), media_type="text/plain", headers=STREAM_HEADERS)


# ── [4교시 변형] SSE — EventSource / @microsoft/fetch-event-source 로 소비 ──
@app.post("/chat/sse")
async def chat_sse(req: ChatRequest):
    async def gen():
        try:
            async for piece in _token_stream(req.message, req.temperature):
                # SSE 프레임: 한 메시지는 "data: ...\n\n" (개행은 공백으로 치환해 프레임 보호)
                yield f"data: {piece.replace(chr(10), ' ')}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: [ERROR] {type(e).__name__}: {e}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream", headers=STREAM_HEADERS)


# ── [5교시] WebSocket 양방향 챗 — 한 연결로 여러 질문 연속 처리 ──────────────
@app.websocket("/ws/chat")
async def ws_chat(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            msg = await ws.receive_text()
            async for piece in _token_stream(msg, 0.3):
                await ws.send_text(piece)
            await ws.send_text("[DONE]")
    except WebSocketDisconnect:
        print("[ws] client disconnected")
