from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
# from llama_index.embeddings.openai import OpenAIEmbedding
# from llama_index.llms.openai import OpenAI
# from llama_index.llms.anthropic import Anthropic

from src.utils import format_docs
# from src.prompt import prompt
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

# LLM
# llm = OpenAI(
#     model_name="gpt-3.5-turbo-instruct",
#     # model_name="gpt-4o",  
#     # temperature=0.2,
#     max_tokens=512,
#     streaming=True
# )
# llm = ChatOllama(model="mistral:latest")
# llm = ChatOllama(model="mistral:latest", base_url="http://ollama_dev:11434")
# llm = ChatOllama(model="mistral:latest", base_url=os.getenv("OLLAMA_BASE_URL"))
# llm = Ollama(model="mistral:latest", temperature=0.1, request_timeout=360000)
# llm = Ollama(model="mistral:latest", base_url="http://192.168.1.209:11435", temperature=0.1, request_timeout=360000)
llm = Ollama(model="mistral:latest", base_url="http://192.168.1.203:11435", temperature=0.1, request_timeout=360000)
# llm = Ollama(model="mistral:latest", base_url=os.getenv("OLLAMA_BASE_URL"))
# llm = Ollama(model="llama-3.2-Korean-Bllossom-3B:latest", base_url="http://192.168.1.209:11435", temperature=0.1, request_timeout=360000)     # 건영 10/7 수정
# llm = AnthropicLLM(model="claude-2.1")

# embed_model = OpenAIEmbedding()
# HuggingFaceEmbeddings 초기화
embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")        
# print(" main.py ---------------> 1. embed_model ", embed_model)


# Vector Store
vector_store = PGVectorStore.from_params(
    database    = "skku",
    host        = "192.168.1.239",
    password    = "aithepwd8#",
    port        = "55432",
    user        = "aitheuser1",
    schema_name = "public",
    table_name  = "tmp_chatbot",
    embed_dim   = 384,     # embed_model에 따라 dimention 변경
)

index = VectorStoreIndex.from_vector_store(vector_store=vector_store)  

class CustomPostprocessor(BaseNodePostprocessor):       # 주원9/27 https://docs.llamaindex.ai/en/stable/module_guides/querying/node_postprocessors/
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

# 검색을 위한 retriever 생성
# retriever = index.as_retriever(similarity_top_k=3)

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
        print("query ", query)

        print("query_engine ", query_engine)
        answer = query_engine.query(query)
        print("answer ", answer)


        # answer = rag_chain.invoke(query.question).strip()
        return {"answer": answer}
    except Exception as e:
        print(e)
        return {"answer": str(e)}
