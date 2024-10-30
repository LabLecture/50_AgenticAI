from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.runnables import RunnablePassthrough
# from langchain_openai import OpenAI, OpenAIEmbeddings
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain_chroma import Chroma
# from langchain_community.chat_models import ChatOllama

from llama_index.core import VectorStoreIndex, PromptTemplate, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.core import StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import Settings
import json
import chromadb

from src.utils import format_docs
# from src.prompt import prompt
from src.prompt_llamaIndex import prompt
from dotenv import load_dotenv
import os

load_dotenv()
app = FastAPI()

# LLM
# llm = OpenAI(
#     model_name="gpt-3.5-turbo-instruct",
#     temperature=0.2,
#     max_tokens=512,
#     streaming=True
# )
# llm = ChatOllama(model="mistral:latest")
# llm = ChatOllama(model="mistral:latest", base_url="http://ollama_dev:11434")
# llm = ChatOllama(model="mistral:latest", base_url=os.getenv("OLLAMA_BASE_URL"))
llm = Ollama(model="mistral:latest", temperature=0.1, request_timeout=360000)
llm = Ollama(model="mistral:latest", base_url="http://192.168.1.209:11435", temperature=0.1, request_timeout=360000)
# llm = Ollama(model="mistral:latest", base_url=os.getenv("OLLAMA_BASE_URL"))
# llm = Ollama(model="llama-3.2-Korean-Bllossom-3B:latest", base_url="http://192.168.1.209:11435", temperature=0.1, request_timeout=360000)     # 건영 10/7 수정

# embeddings_model = OpenAIEmbeddings()
# HuggingFaceEmbeddings 초기화
embeddings_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")        
print(" main.py ---------------> 1. embeddings_model ", embeddings_model)

# Vector Store
# db = Chroma(persist_directory="./vector_store", embedding_function=OpenAIEmbeddings())
# db = Chroma(persist_directory="./vector_store", embedding_function=embeddings_model)

# retriever = db.as_retriever(search_type="similarity")

# ChromaDB 클라이언트 생성 및 기존 컬렉션 로드
chroma_client = chromadb.PersistentClient(path="./vector_store")
chroma_collection = chroma_client.get_collection("my_collection")

# ChromaVectorStore 생성
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

# StorageContext 생성
storage_context = StorageContext.from_defaults(vector_store=vector_store)
Settings.embed_model = embeddings_model

# VectorStoreIndex 생성 (이미 존재하는 vector store 사용)
index = VectorStoreIndex.from_vector_store(
    vector_store,
    storage_context=storage_context,
    # embedding_function=embeddings_model,
)

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

# llama_index
query_engine = index.as_query_engine(
    llm=llm,                               
    similarity_top_k=3,
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
    