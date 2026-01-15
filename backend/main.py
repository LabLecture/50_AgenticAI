from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.output_parsers import StrOutputParser   # 문자열 출력 파서
from langchain_core.runnables import RunnablePassthrough    # 입력을 그대로 출력하는 러너블
# from langchain_openai import OpenAI, OpenAIEmbeddings       
from langchain_ollama import ChatOllama   
from langchain_huggingface import HuggingFaceEmbeddings     # HuggingFace 임베딩 모델
from langchain_chroma import Chroma
from src.utils import format_docs   # 검색된 문서들을 텍스트 형식으로 변환하는 유틸 함수
from src.prompt import prompt       # 프롬프트 템플릿 
from dotenv import load_dotenv      # .env 환경변수 로드

load_dotenv()       # .env 파일에 정의된 API 키나 환경 변수들을 로드
app = FastAPI()     # [1]. FastAPI 앱 생성

# [2]. 언어 모델(LLM) 설정
# llm = OpenAI(
#     model_name="gpt-3.5-turbo-instruct",
#     temperature=0.2,  # 응답의 창의성(무작위성) 조절
#     max_tokens=512,
#     streaming=True
# )
llm = ChatOllama(model="mistral:latest")

# [3]. 임베딩 모델 설정
# embeddings_model = OpenAIEmbeddings()
# HuggingFaceEmbeddings 초기화
embeddings_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")        

# [4]. Vector Store 및 Retriever 설정
# db = Chroma(persist_directory="./vector_store", embedding_function=OpenAIEmbeddings())
db = Chroma(persist_directory="./vector_store", embedding_function=embeddings_model)
retriever = db.as_retriever(search_type="similarity")   # 유사도(similarity) 기반 검색

# [5]. CORS 설정 (프런트엔드와 백엔드 통신 허용)
origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(         # CORS 설정 (프런트엔드와 백엔드 통신 허용)
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, # 쿠키 허용
    allow_methods=["*"],    # GET, POST 등 모든 메소드 허용
    allow_headers=["*"],    # 모든 헤더 허용
)

# [6]. 데이터 모델 정의
class UserQuery(BaseModel):
    """user question input model"""
    question: str

# [7]. RAG 체인(Chain) 구성 - 핵심 로직
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()  # 최종 출력 파서 설정
)      

# [8]. 챗봇 엔드포인트 정의
@app.post("/chat/")
async def chat(query: UserQuery):
    """chat endpoint"""
    try:
        answer = rag_chain.invoke(query.question).strip()
        return {"answer": answer}   # 응답 반환
    except Exception as e:
        print(e)
    