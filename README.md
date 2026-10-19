# chatbot_light


## 교안 ↔ 실습 소스 브랜치

| 교안 | 브랜치 |
|------|--------|
| D18 LLMOps | `main` |
| D19 Agent2 | `agent` |
| D20 LangGraph | `graph` (graph/1-6), `etc` (MCP), `vllm` (vLLM 문서) |
| D21 LangManus | `langmanus` (+ `step_4_agent_fix`: insert.sql) |
| supp_03~08 | `supp` |

## 실행 전 준비

- **API 키**: `backend/.env.example` → `backend/.env`, `etc/.env.example` → `etc/.env` 로 복사한 뒤 키 값을 채운다. (`.env` 는 git 에 올리지 않는다)
- **벡터 스토어**: `backend/vector_store` 가 없거나 PDF를 바꿨다면 `cd backend/src && python embedding.py` 를 먼저 실행한다. (임베딩: `intfloat/multilingual-e5-small`)
- **Windows 경로 길이**: transformers/HF 캐시가 260자 경로 제한에 걸릴 수 있다. 짧은 경로(예: `C:\work`)에 clone 하거나, 관리자 권한으로 `LongPathsEnabled` 를 켠다.
  ```powershell
  New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name LongPathsEnabled -Value 1 -PropertyType DWORD -Force
  ```
