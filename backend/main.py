from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.llms.openrouter import OpenRouter   # [추가] OpenRouter (main/step2 와 동일)

from src.prompt_llamaIndex import prompt
from dotenv import load_dotenv
import os

from llama_index.core.schema import NodeWithScore          
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.vector_stores.postgres import PGVectorStore

from llama_index.core.schema import NodeWithScore        
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core import QueryBundle
from llama_index.core.schema import NodeWithScore 
from llama_index.core.postprocessor import MetadataReplacementPostProcessor

from typing import List                                     
from typing import Optional

load_dotenv()
app = FastAPI()

# llm = Ollama(model="mistral:latest", base_url="http://192.168.1.203:11435", temperature=0.1, request_timeout=360000)
# llm = Ollama(model="mistral:latest", temperature=0.1, request_timeout=360000)  # 기존: 로컬 Ollama 필요
# ── [변경] main/step2 처럼 OpenRouter 사용 (키는 .env 의 OPENROUTER_API_KEY) ──
llm = OpenRouter(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="openai/gpt-oss-120b:free",
    # model="deepseek/deepseek-v4-flash",
    max_tokens=512,
    temperature=0.2,
    context_window=8192,
)

# HuggingFaceEmbeddings 초기화
embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")        


# Vector Store
vector_store = PGVectorStore.from_params(
    database    = os.getenv("POSTGRES_DB", "hycu_dropout"),     # [변경] 로컬 postgres(.env)
    host        = os.getenv("POSTGRES_HOST", "localhost"),
    password    = os.getenv("POSTGRES_PASSWORD"),
    port        = os.getenv("DB_PORT", "5432"),
    user        = os.getenv("POSTGRES_USER"),
    schema_name = "public",
    # ⚠ PGVectorStore 는 table_name 앞에 자동으로 'data_' 를 붙인다.
    #   → 실제 물리 테이블이 public.data_tmp_chatbot_00(61행) 이므로 여기엔 접두어 없이 "tmp_chatbot_00" 을 넣어야 한다.
    #   ("data_tmp_chatbot_00" 을 넣으면 data_data_tmp_chatbot_00(0행)을 찾아 검색 0건→'Empty Response')
    table_name  = "tmp_chatbot_00",
    embed_dim   = 384,                          # embed_model에 따라 dimention 변경
)

# index = VectorStoreIndex.from_vector_store(vector_store=vector_store)  

class CustomPostprocessor(BaseNodePostprocessor):       
    def _postprocess_nodes(
        self, nodes: List[NodeWithScore], query_bundle: Optional[QueryBundle]
    ) -> List[NodeWithScore]:
        # [변경] 검색된 노드를 사건 발생 시각(time_start) 오름차순으로 정렬한다.
        #        → "사건을 시간순으로 정리해줘" 질문에서 LLM 이 시간순으로 답하도록 컨텍스트를 정렬.
        #        (기존엔 정렬 없이 디버그 출력만 했고, xlsx 노드엔 file_name 메타가 없어 KeyError 발생)
        def _sort_key(nws):
            ts = str(nws.node.metadata.get("time_start", "") or "").strip()
            return (ts == "", ts)   # 값 없으면 맨 뒤로, 있으면 ISO 문자열(예: 2021-02-16) 오름차순
        return sorted(nodes, key=_sort_key)

custom_postprocessor = CustomPostprocessor()
node_postprocessors = [custom_postprocessor]
node_postprocessors.append(MetadataReplacementPostProcessor(target_metadata_key="window"))

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserQuery(BaseModel):
    """user question input model"""
    question: str
    
# LangChain
# rag_chain = (
#     {"context": retriever | format_docs, "question": RunnablePassthrough()}
#     | prompt
#     | llm
#     | StrOutputParser()
# )   

# Storage Context 생성 및 임베딩 모델 설정
storage_context = StorageContext.from_defaults(
    vector_store=vector_store,
)

# VectorStoreIndex 초기화시 임베딩 모델 지정
index = VectorStoreIndex.from_vector_store(
    vector_store=vector_store,
    storage_context=storage_context,
    embed_model=embed_model  # 중요: 임베딩 모델 명시적 지정
)

# llama_index
query_engine = index.as_query_engine(
    llm=llm,     
    similarity_top_k=10,
    node_postprocessors=node_postprocessors
)

qa_prompt_key = "response_synthesizer:text_qa_template"
# query_engine.update_prompts(prompt)   # 기존: dict 가 아니라 PromptTemplate 만 넘겨 미적용
query_engine.update_prompts({qa_prompt_key: prompt})

@app.post("/chat/")
# async def chat(query: UseQuery):
async def chat(request: Request):
    """chat endpoint"""
    try:
        body = await request.json()
        print("body ----> ", body)
        query = body["query"]
        print("query ----> ", query)
        response = query_engine.query(query)
        print("response ----> ", response)
        answer = response.response  # 여기를 수정
        # answer = query_engine.query(query)
        # answer = rag_chain.invoke(query.question).strip()
        print("answer ----> ", answer)
        return {"answer": answer}
    except Exception as e:
        print("Error:", str(e))
        return {"answer": str(e)}

if __name__ == "__main__":
    import uvicorn
    # step2 와 동일: 앱 객체로 단일 로드(임베딩 모델+DB 중복 로드 방지). 포트 8002.
    # hot-reload 가 필요하면 CLI:  uvicorn main:app --reload --host 0.0.0.0 --port 8002
    uvicorn.run(app, host="0.0.0.0", port=8002)