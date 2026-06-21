"""
04_api.py — 헬프데스크 에이전트 FastAPI 백엔드.

supp_08 React 프론트(test/chat-frontend)를 그대로 재사용한다:
  POST /chat  {"message": "...", "thread_id": "web"}  →  {"reply": "..."}

실행:
  cd supp/supp_03/demo_helpdesk
  ../../venv/Scripts/python.exe -m uvicorn 04_api:app --port 8001
프론트는 test/chat-frontend 에서 npm start (API=http://localhost:8001 이미 설정됨).
"""
import importlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

_graph_mod = importlib.import_module("02_graph")

app = FastAPI(title="(주)다희 사내 헬프데스크 에이전트")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_graph = _graph_mod.build_graph()   # MemorySaver 가 thread_id 별 멀티턴 유지


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "web"


class ChatResponse(BaseModel):
    reply: str
    trace: list[str]


@app.get("/health")
def health():
    return {"status": "ok", "demo": "helpdesk-agent"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    result = _graph_mod.run_turn(_graph, req.thread_id, req.message)
    return ChatResponse(reply=result["answer"], trace=result.get("trace", []))
