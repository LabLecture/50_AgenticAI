from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama

from src.prompt_llamaIndex import prompt
from dotenv import load_dotenv

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

llm = Ollama(model="mistral:latest", base_url="http://192.168.1.203:11435", temperature=0.1, request_timeout=360000)

# HuggingFaceEmbeddings 초기화
embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")        


# Vector Store
vector_store = PGVectorStore.from_params(
    database    = "skku",
    host        = "192.168.1.239",
    password    = "aithepwd8#",
    port        = "55432",
    user        = "aitheuser1",
    schema_name = "public",
    table_name  = "tmp_chatbot",
    embed_dim   = 384,                          # embed_model에 따라 dimention 변경
)

index = VectorStoreIndex.from_vector_store(vector_store=vector_store)  

class CustomPostprocessor(BaseNodePostprocessor):       
    def _postprocess_nodes(
        self, nodes: List[NodeWithScore], query_bundle: Optional[QueryBundle]
    ) -> List[NodeWithScore]:
        print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        for n in nodes:
            print("nodes\n" + n.metadata['file_name'])
            # print(n.metadata['document_name'])
            print(n)
            print("query_bundle\n")
            print(query_bundle)
            # n.score -= 1      # 스코어를 조정하거나 없으면 제외되니 OK

        return nodes

custom_postprocessor = CustomPostprocessor()
node_postprocessors = [custom_postprocessor]
node_postprocessors.append(MetadataReplacementPostProcessor(target_metadata_key="window"))

origins = [
    "http://localhost",
    "http://localhost:3000",
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
# query_engine.update_prompts({qa_prompt_key: prompt})
query_engine.update_prompts(prompt)

@app.post("/chat/")
# async def chat(query: UseQuery):
async def chat(request: Request):
    """chat endpoint"""
    try:
        body = await request.json()
        query = body["query"]

        answer = query_engine.query(query)
        # answer = rag_chain.invoke(query.question).strip()
        return {"answer": answer}
    except Exception as e:
        print(e)
        return {"answer": str(e)}
