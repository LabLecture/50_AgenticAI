# 16_graphrag_demo — Microsoft GraphRAG 최소 데모 (4교시 선택 실습)

작은 텍스트 1개로 Microsoft `graphrag` 의 **index → Global Search query** 를 끝까지 돌려보는 최소 데모.
4교시는 본래 이론이지만, "한 번 직접 돌려보고 싶다"는 분을 위한 **선택 실습**입니다.

## ⚠️ 먼저 읽기
- graphrag 는 의존성이 무겁고 메인 `supp/venv`(langchain 1.x)와 충돌할 수 있어 **별도 venv** 를 씁니다.
- **임베딩 없이 Global Search 만** 도는 최소 구성입니다 — OpenRouter 에는 임베딩 API 가 없어, `settings.yaml` 의 `workflows` 에서 `generate_text_embeddings` 단계를 뺐습니다. 그래서 임베딩이 필요한 **Local / DRIFT / Basic search 는 미지원**(Global 만 가능).
- LLM 은 **OpenRouter `openai/gpt-4.1-nano`** (저비용). 텍스트가 작아 index 비용은 보통 수 센트 이하.

## 1) 설치 (별도 venv — ⚠️ Windows는 venv를 *짧은 경로*에!)
> ⚠️ **Windows MAX_PATH(260자)**: venv 를 이 폴더 안(`16_graphrag_demo\venv`)에 만들면 의존성 `litellm` 의 매우 긴 파일 경로가 260자를 넘어
> `pip install graphrag` 가 `OSError: [Errno 2] No such file or directory: ...litellm\proxy\guardrails\...json` 로 실패합니다.
> → **venv 를 짧은 경로(예 `D:\grvenv`)에 만드세요.**
```powershell
python -m venv D:\grvenv          # ← 짧은 경로 (이 폴더 안 X)
D:\grvenv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install graphrag              # 검증: 3.1.0
```
> 또는 **관리자 권한**으로 긴 경로를 한 번 켜면 폴더 안 venv 도 됩니다:
> `reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled /t REG_DWORD /d 1 /f` → **새 셸**에서 재시도.

## 2) 키 설정
`.env.example` 를 `.env` 로 복사 후 OpenRouter 키 입력:
```
GRAPHRAG_API_KEY=sk-or-v1-...
```

## 3) 실행
```powershell
cd supp\supp_04\16_graphrag_demo  # 데모 폴더로 (venv 는 D:\grvenv 활성화 상태)
$env:PYTHONIOENCODING="utf-8"     # Windows 한글/유니코드 출력 깨짐 방지
# 참고: 실행 중 LiteLLM 의 botocore/Bedrock/SageMaker 경고는 무시 (AWS 미사용, OpenRouter 사용)

# 인덱싱 — 그래프/커뮤니티/리포트 생성 (임베딩 skip 구성이라 --skip-validation 필수)
graphrag index --root . --skip-validation

# Global Search 질의
graphrag query --root . --method global "What are the main themes and key relationships in this text?"
```

## 동작 원리 (4교시 이론과 연결)
- `index` : 텍스트 → **엔티티/관계 추출**(extract_graph) → **커뮤니티 탐지**(create_communities, Leiden) → **계층 요약**(create_community_reports). = 4.2~4.3 인덱싱 파이프라인.
- `query --method global` : 커뮤니티 리포트들을 **map-reduce** 로 종합해 "전체의 주요 테마는?" 같은 *전역 요약형* 질문에 답함. = 4.4 Global Search.

## 검증된 출력 (예시)
> Q: *"What are the main themes and key relationships in this text?"*
> → "AI 안전·윤리에 대한 집중", "모델 개발사–클라우드–투자자 생태계", "파트너십의 함의" 등을
>   `[Data: Reports (...)]` 인용과 함께 종합 요약. (gpt-4.1-nano, 임베딩 0회)

## 구조
```
16_graphrag_demo/
├── input/sample.txt   # 입력 텍스트 (작게 — AI 기업 관계 ~200단어)
├── settings.yaml      # graphrag 설정 (OpenRouter nano + 임베딩 skip workflows)
├── prompts/           # 추출/리포트 프롬프트 (graphrag init 기본값)
├── .env.example       # GRAPHRAG_API_KEY
└── (생성물) output/ cache/ logs/ venv/   ← gitignore
```

## 한계 / 참고
- 이건 *맛보기* 데모다. 실무 규모(수천 페이지)에선 index 비용·시간이 급증 → 4교시 본문에서 다룬 trade-off 가 그대로 적용된다.
- 임베딩까지 쓰고 싶으면(Local/DRIFT search) OpenAI(또는 로컬 임베딩 서버) 임베딩 엔드포인트를 `embedding_models` 에 연결하고 `workflows` 에서 `generate_text_embeddings` 를 복원하면 된다.
