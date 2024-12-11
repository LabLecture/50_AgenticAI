from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import OpenAI, OpenAIEmbeddings
from langchain_openai import ChatOpenAI
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain_chroma import Chroma

# from src.utils import format_docs
from src.prompt import prompts
from dotenv import load_dotenv

from langchain_community.chat_models import ChatOllama
from langchain_community.document_loaders import UnstructuredExcelLoader
# from langchain.prompts import ChatPromptTemplate
import os
from typing import Optional, Dict
import json

##########################
from langchain_core.tools import tool
#from langchain.agents import Tool
from typing import Annotated
from langchain_core.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory 
from langchain.globals import set_verbose, set_debug
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import PGVector
from sqlalchemy import create_engine
set_verbose(True)
set_debug(True)
##########################

from db import PostgreSqlDB
import db_sql
import src.agent_prompt as agent_prompt

class UserQuery(BaseModel):
    question: str
    conversation_id: Optional[str] = None
    current_step: Optional[str] = None

class ConversationState:
    def __init__(self):
        self.conversations: Dict[str, dict] = {}

    def get_conversation(self, conv_id: str) -> dict:
        if conv_id not in self.conversations:
            self.conversations[conv_id] = self.create_new_conversation()
        return self.conversations[conv_id]

    def create_new_conversation(self) -> dict:
        return {
            "intent": None,
            "current_step": None,
            "context": {},
            "history": []
        }

    def reset_conversation(self, conv_id: str):
        """대화 상태를 초기화합니다."""
        self.conversations[conv_id] = self.create_new_conversation()

    def update_conversation(self, conv_id: str, intent: Optional[str] = None, 
                          current_step: Optional[str] = None, 
                          context: Optional[dict] = None,
                          history: Optional[list] = None):
        conv = self.get_conversation(conv_id)
        if intent:
            conv["intent"] = intent
        if current_step:
            conv["current_step"] = current_step
        if context:
            conv["context"].update(context)
        if history:
            conv["history"].extend(history)

load_dotenv()
app = FastAPI()
conversation_state = ConversationState()
postrgre_db = PostgreSqlDB()

# LLM
# llm = OpenAI(
llm = ChatOpenAI(
    # model_name="gpt-3.5-turbo-instruct",
    # model_name="gpt-4",       # 'This is a chat model and not supported in the v1/completions endpoint. Did you mean to use v1/chat/completions?
    # model_name="gpt-4o-mini",   # 상동
    model="gpt-4o",   #
    temperature=0.2,
    # max_tokens=512,
    max_tokens=256,
    streaming=True
)

# llm = ChatOllama(model="llama-3-Korean-Bllossom-8B:latest", base_url="http://192.168.1.209:11435", temperature=0.1, request_timeout=360000)     # 건영 10/7 수정

# loader = UnstructuredExcelLoader("./backend/data/웅진씽크백FAQ_PGVector_Data.xlsx", mode="elements")
# docs = loader.load()
# collection_name = "my_docs"

# collection_name="graywhale",
vector_store = PGVector(
    collection_name= "my_docs",
    embeddings=OpenAIEmbeddings(model="text-embedding-3-large"),
    connection=os.environ["POSTGRESQL_CONNECTION_VECTORSTORE_STRING"],
    use_jsonb=True,
)

# vector_store.add_documents(docs)

# retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 1})

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

intent_chain    = (prompts["intent_classifier"]     | llm   | StrOutputParser() ) # 체인 초기화
greeting_chain  = (prompts["greeting"]              | llm   | StrOutputParser() ) # greeting 체인 정의

# 업무별 체인 정의
prompt_chains = {
    "ACCOUNT_MANAGEMENT":   prompts["account_management"]    | llm | StrOutputParser(),
    "LOAN_EXTENSION":       prompts["loan_extension"]        | llm | StrOutputParser(),
    "TRANSACTION_HISTORY":  prompts["transaction_history"]   | llm | StrOutputParser(),
    "CUSTOMER_INFO":        prompts["customer_info"]         | llm | StrOutputParser(),
    "SEARCH_USER_INFO":     prompts["search_user_info"]      | llm | StrOutputParser(),
    "SEARCH_CLASS_PROGRESS":     prompts["class_progress"]      | llm | StrOutputParser(),
}

human = """
{input}

{agent_scratchpad}

(reminder to respond in a JSON blob no matter what)"""

##########################
# 이 코드안에 있는 문자열 자체도 LLM이 사용하는 거임..

    
@tool
def get_user_class_info( # default 값에 따라 받아오는 값이 달라짐 (ex) 6, 6학년 이런게 달라짐..
    user_name:Annotated[str, "학생(자녀)이름, default value is **샘플스**"],
    user_school:Annotated[str, "학교, default value is **샘플학교**"],
    user_grade:Annotated[int, "학년, default value is **7**"]
    # ) -> dict:
    ) -> str:
    """학생(자녀)의 **수업정보**를 체크(조회,확인)합니다.
        추가적인 지시사항:
        - 유저 이름이나 학교명이 구체적으로 명시되지 않은 경우(예: '제 딸', '초등학교' 등), 해당 정보는 수집하지 마십시오.
        - 구체적인 이름과 학교명이 제공된 경우에만 user_name과 user_school을 설정하십시오.
        - 일반적인 명칭이 입력된 경우 "안녕하세요 웅진씽크빅 챗봇입니다. 자녀의 이름과 학교명을 구체적으로 알려주세요."라고 응답하십시오.
    """
    # Parameters for the request

    class_datas = postrgre_db.fetch_all(db_sql.select_class_info, (user_name, user_school, user_grade))

    if class_datas is None:
        return f'''
            입력 정보에 부합되는 수업정보가 없습니다.
            다시 자녀정보를 입력해주세요.
        '''
    return f'''
    학생(자녀)이름:{user_name}
    학교:{user_school}
    학년:{user_grade}
    수업명:{class_datas}
    '''
    


@tool
def get_user_class_progress_info(
    user_name:Annotated[str, "학생(자녀)이름, default value is **샘플스**"],
    class_data:Annotated[str, "수업이름, default value is **샘플**"],
    class_id:Annotated[str, "수업번호, default value is **0**"]
    ) -> str:
    """학생(자녀)의 **수업진도**를 체크(조회,확인)합니다.
        추가적인 지시사항: 
        - "'수업이름' ....", "'수업번호'. '수업이름' 수업 ....", "'수업번호' ....", 과 같은 형식의 질문을 받아야합니다.("...."는 추가로 붙을 수 있는 말입니다.('이요', '입니다' 등등))
        - 위 형식외의 질문은 받으면 안됩니다.
        - "'수업이름' ...." 이 형식의 경우 수업번호는 default 값이고 수업이름은 '수업이름' 입니다.
        - "'수업번호'. '수업이름' 수업 ...." 이 형식의 경우 수업번호는 '수업번호' 이고 수업이름은 '수업이름' 입니다.
        - "'수업번호' ...." 이 형식의 경우 수업번호는 '수업번호' 이고 수업이름은 default 값입니다.
    """
    # Parameters for the request

    class_progress_data = postrgre_db.fetch_one(db_sql.select_class_progress_info_02, (user_name, f"%{class_data}%", class_id))

    if class_progress_data is None:
        return f'''
            입력 정보에 부합되는 수업진도가 없습니다.
            다시 자녀정보를 입력해주세요.
        '''
        raise ValueError('해당 유저의 데이터가 존재하지 않습니다')
    
    return f'''
    학생(자녀)이름:{user_name}
    수업진도:{class_progress_data}
    '''
    
@tool
def explain_class_progress_info(query : str) -> str:
    """학생(자녀)의 수업정보 및 수업진도를 확인하기 위한 방법을 설명합니다."""
    # Parameters for the request
    
    return f'''
        안녕하세요 웅진씽크빅 챗봇입니다.
        자녀분 수업진도를 체크하려고 하시는 군요? 우선 자녀분 아이디나 학교/학년/이름을 말씀해 주실 수 있나요?
    '''
    
# RAG 검색을 수행하는 도구 정의
# @tool
# def search_knowledge_base(query: str) -> str:
#     """
#     웅진씽크빅 FAQ에 관련된 질문을 검색합니다.
#     """
    
#     try:
#         # RAG 체인 실행
#         response = retriever.invoke(query)
#         result = response[0].page_content.split('답변 : ')[-1].strip()
#         return result
#     except Exception as e:
#         return f"지식베이스 검색 중 오류가 발생했습니다: {str(e)}"

# RAG 검색을 수행하는 도구 정의
# @tool
# def search_knowledge_base(query: str) -> str:
#     """
#     웅진씽크빅 FAQ에 관련된 질문을 검색합니다.
#     """
    
#     try:
#         # RAG 체인 실행
#         response = retriever.invoke(query)
#         result = response[0].page_content.split('답변 : ')[-1].strip()
#         return result
#     except Exception as e:
#         return f"지식베이스 검색 중 오류가 발생했습니다: {str(e)}"


memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

class_progress_agent = create_structured_chat_agent(
        llm, 
        # [get_user_class_info, get_user_class_progress_info, explain_class_progress_info, search_knowledge_base],
        [get_user_class_info, get_user_class_progress_info, explain_class_progress_info],
        ChatPromptTemplate.from_messages(
            [
                ("system", agent_prompt.search_class_prompt), 
                MessagesPlaceholder("chat_history", optional=True),
                ("human", human)
            ]
        )
    )


class_progress_agent_executor = AgentExecutor(
    agent=class_progress_agent,
    # tools=[get_user_class_info, get_user_class_progress_info, explain_class_progress_info, search_knowledge_base],
    tools=[get_user_class_info, get_user_class_progress_info, explain_class_progress_info],
    # tools=[get_user_class_info,  explain_class_progress_info],
    # verbose=True,
    handle_parsing_errors=True,
    memory=memory,
    max_iterations=100,
)

##########################

@app.post("/chat/")
async def chat(query: UserQuery):
    try:
        # test_data = postrgre_db.fetch_all(db_sql.select_test, ("이웅진",))
        # response_01 = retriever.invoke("인터넷으로 접수했는데 제출서류는 언제 제출하나요?")
        
        conv = conversation_state.get_conversation(query.conversation_id)
        conv["intent"] = "SEARCH_CLASS_PROGRESS" # 웅진챗봇으로 고정
        print(" -------------------------> query : ", query)
        print(" conv : ", conv)
        previous_intent = conv["intent"]        # 이전 의도 저장
        previous_step = conv["current_step"]    # 이전 단계 저장
        
        if not conv["intent"]:                  # 의도 분석 (새로운 대화이거나 분류 불가능한 이전 상태인 경우)
            intent = intent_chain.invoke({"question": query.question}).strip() # 이렇게 그냥 프롬프트를 맞춰서 보내면 intent를 리턴해줌;;
            
            if "None" in intent or intent not in prompt_chains.keys():  # 분류 불가능한 경우 처리                
                if previous_intent:                                     # 이전 상태가 있었다면 그 상태 유지
                    greeting_response = "죄송합니다. 질문을 이해하지 못했습니다. 이전 문의하신 내용을 계속 진행하시겠습니까?"
                    
                    conv["intent"] = previous_intent                    # 이전 상태로 복원
                    conv["current_step"] = previous_step
                    
                    return {
                        "answer": greeting_response,
                        "intent": previous_intent,
                        "current_step": previous_step,
                        "is_reset": False
                    }
                else:
                    # 완전히 새로운 대화인 경우
                    greeting_response = "안녕하세요! 은행 고객센터입니다. 어떤 도움이 필요하신가요?\n\n다음 서비스를 제공해드릴 수 있습니다:\n1. 계좌 조회 및 관리\n2. 주택담보대출 만기연장\n3. 거래 내역 확인\n4. 고객 정보 업데이트"
                    return {
                        "answer": greeting_response.strip(),
                        "intent": None,
                        "current_step": None,
                        "is_reset": True
                    }            
            
            conv["intent"] = intent                     # 정상적인 의도 분류된 경우
        
        if conv["intent"] == "SEARCH_CLASS_PROGRESS" :
            chat_history = memory.buffer_as_messages
            
            response = class_progress_agent_executor.invoke({
                "input": query.question,
                "chat_history": chat_history,
            })
            print(response)
            return {
                "answer": response['output'],
                "intent": conv["intent"],
                "current_step": conv["current_step"],
                "is_reset": False, 
                "context": conv["context"]              # 현재 컨텍스트 상태도 반환
            }
                    
        

        
    except Exception as e:
        print(e)
        return {"error": str(e)}
    
