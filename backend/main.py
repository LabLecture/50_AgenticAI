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
from langchain.memory import ConversationBufferMemory
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
            "next_DB": False,    # 고객 답변을 받아 llm 전 DB처리를 위함.
            "is_reset": False,
            "infos": {},         # 학생 정보 등 정보 저장을 위함
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
# llm = ChatOpenAI(
#     # model_name="gpt-3.5-turbo-instruct",
#     # model_name="gpt-4",       # 'This is a chat model and not supported in the v1/completions endpoint. Did you mean to use v1/chat/completions?
#     # model_name="gpt-4o-mini",   # 상동
#     model="gpt-4o",   #
#     temperature=0.2,
#     max_tokens=512,
#     streaming=True
# )

llm = ChatOllama(model="mistral:latest", base_url="http://192.168.1.209:11435", temperature=0.1, request_timeout=360000)     # 건영 10/7 수정
# llm = AnthropicLLM(model="claude-2.1")


# vector_store = PGVector(
#     embeddings=OpenAIEmbeddings(model="text-embedding-3-large"),
#     collection_name="graywhale",
#     connection=os.environ["POSTGRESQL_CONNECTION_VECTORSTORE_STRING"],
#     use_jsonb=True,
# )

# retriever_3     =vector_store.as_retriever(search_type="similarity",search_kwargs={"k": 3}),      # retriever
# retriever_60    =vector_store.as_retriever(search_type="similarity",search_kwargs={"k":60}),      # 

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

##########################
# 이 코드안에 있는 문자열 자체도 LLM이 사용하는 거임..

    
@tool
def get_user_class_info( # default 값에 따라 받아오는 값이 달라짐 (ex) 6, 6학년 이런게 달라짐..
    user_name:Annotated[str, "학생(자녀)이름, default value is **샘플스**"],
    user_school:Annotated[str, "학교, default value is **샘플학교**"],
    user_grade:Annotated[int, "학년, default value is **7**"]
    # ) -> dict:
    ) -> str:
    """ **학생(자녀)정보**를 조회합니다.
    추가적인 지시사항:
    - 유저 이름이나 학교명이 구체적으로 명시되지 않은 경우(예: '제 딸', '초등학교' 등), 해당 정보는 수집하지 마십시오.
    - 구체적인 이름과 학교명이 제공된 경우에만 user_name과 user_school을 설정하십시오.
    - 일반적인 명칭이 입력된 경우 "우선 자녀분 아이디나 학교/학년/이름을 말씀해 주실 수 있나요? "라고 응답하십시오.
    """
    # Parameters for the request

    class_datas = postrgre_db.fetch_all(db_sql.select_class_info, (user_name, user_school, user_grade))

    if class_datas is None:
        raise ValueError('해당하는 자녀정보가 없습니다. 다시 확인하고 입력해주세요.')
        return f'''
            안녕하세요 웅진씽크빅 챗봇입니다.
            자녀분 수업진도를 체크하려고 하시는 군요? 우선 자녀분 아이디나 학교/학년/이름을 말씀해 주실 수 있나요?
        '''
    
    return f'''
    학생(자녀)이름:{user_name}
    학교:{user_school}
    학년:{user_grade}
    '''
    
    
@tool
def get_user_class_progress_info(
    user_name:Annotated[str, "학생(자녀)이름, default value is **샘플스**"],
    class_data:Annotated[str, "수업명, default value is **샘플**"],
    class_id:Annotated[str, "수업번호, default value is **0**"]
    ) -> str:
    """학생(자녀)의 **수업진도**를 체크(조회,확인)합니다.
        추가적인 지시사항:
        - 유저 이름이나 학교명이 구체적으로 명시되지 않은 경우(예: '제 딸', '초등학교' 등), 해당 정보는 수집하지 마십시오.
        - 구체적인 이름과 학교명이 제공된 경우에만 user_name과 user_school을 설정하십시오.
        - 일반적인 명칭이 입력된 경우 "우선 자녀분 아이디나 학교/학년/이름을 말씀해 주실 수 있나요? "라고 응답하십시오.
        - 수업번호나 수업이름이 구체적으로 명시되지 않은 경우, 해당 정보는 수집하지 마십시오.
        - 숫자를 입력받으면 해당 내용은 수업번호이고 문자열을 입력받으면 해당 내용은 수업명입니다.
        - 수업명 뒤에 "수업"이라는 문자가 있다면 해당 문자와 공백은 제거하십시오.
    """
    # Parameters for the request
    class_progress_data = postrgre_db.fetch_one(db_sql.select_class_progress_info_02, (user_name, f"%{class_data}%", class_id))
    if class_progress_data is None:
        return f'''
            안녕하세요 웅진씽크빅 챗봇입니다.
            자녀분 수업진도를 체크하려고 하시는 군요? 우선 자녀분 아이디나 학교/학년/이름을 말씀해 주실 수 있나요?
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
    
human = '''

{input}

{agent_scratchpad}

(reminder to respond in a JSON blob no matter what)'''
# 각 system, human 내용 잘 읽어보기 이 내용 자체가 함수임..(프롬프트가 말로하는 코딩이라 생각하면됨)


memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

agent_user = create_structured_chat_agent(
        llm, 
        [get_user_class_info],
        ChatPromptTemplate.from_messages(
            [
                ("system", agent_prompt.search_prompt_user), 
                MessagesPlaceholder("chat_history", optional=True),
                ("human", human)
            ]
        )
    )


agent_user_executor = AgentExecutor(
    agent=agent_user,
    tools=[get_user_class_info],
    # verbose=True,
    handle_parsing_errors=True,
    memory=memory,
    max_iterations=5,
)

agent_user_class = create_structured_chat_agent(
        llm, 
        [get_user_class_info, get_user_class_progress_info],
        ChatPromptTemplate.from_messages(
            [
                ("system", agent_prompt.search_prompt_user_class), 
                MessagesPlaceholder("chat_history", optional=True),
                ("human", human)
            ]
        )
    )


agent_user_class_executor = AgentExecutor(
    agent=agent_user_class,
    tools=[get_user_class_info, get_user_class_progress_info],
    # verbose=True,
    handle_parsing_errors=True,
    memory=memory,
    max_iterations=5,
)

agent_progress = create_structured_chat_agent(
        llm, 
        [get_user_class_info, get_user_class_progress_info, explain_class_progress_info],
        ChatPromptTemplate.from_messages(
            [
                ("system", agent_prompt.search_class_progress_prompt), 
                MessagesPlaceholder("chat_history", optional=True),
                ("human", human)
            ]
        )
    )

agent_progress_executor = AgentExecutor(
    agent=agent_progress,
    tools=[get_user_class_info, get_user_class_progress_info, explain_class_progress_info],
    # verbose=True,
    handle_parsing_errors=True,
    memory=memory,
    max_iterations=5,
)

##########################


chain_intent = {        # 체인 정의 (중간 의도 파악용, 답변 활용X)
    "INTENT"                    :   prompts["intent_classifier_0"]                  | llm | StrOutputParser(),  # 기본 의도 파악
    "INTENT_LEARNING_SUPPORT"   :   prompts["intent_classifier_3_learning_support"] | llm | StrOutputParser(),  # 기본 의도 파악
    "INTENT_RECRUITMENT"        :   prompts["intent_classifier_23_recruitment"] | llm | StrOutputParser()   # 교사or직원채용 의도파악용
}
chains_prompt = {
    "GREETING"              :   prompts["greeting_0"]               | llm | StrOutputParser(),  # 단순인사 prompt
    "MEMBERSHIP"            :   prompts["membership_management_1"]  | llm | StrOutputParser(),
    "LEARNING_SUPPORT"      :   prompts["learning_support"]         | llm | StrOutputParser(),
    "TECHNICAL_SUPPORT"     :   prompts["technical_support"]        | llm | StrOutputParser(),
    "GENERAL_INQUIRIES"     :   prompts["general_inquiries"]        | llm | StrOutputParser()
}

# 에러 해결 요망 start ----------------> 
# chains_rag = {
#     "TEACHER_RECRUITMENT"   :   prompts["teacher_recruitment_2_1"]  | {"context": retriever_3}  | llm | StrOutputParser(), 
#     "EMPLOYEE_RECRUITMENT"  :   prompts["employee_recruitment_2_2"] | {"context": retriever_3}  | llm | StrOutputParser(), 
#     "IR"                    :   prompts["IR"]                       | {"context": retriever_60} | llm | StrOutputParser()  
# }
# chains_rag = (    # 단순 소스 백업 (동작 후 삭제 예정)
#     {"context": retriever | format_docs, "question": RunnablePassthrough()}
#     | prompts["intent_teacher_recruitment"]
#     | llm
#     | StrOutputParser()
# ) 
# 에러 해결 요망 end ----------------> 
str_LEARNING_SUPPORT = {
    "CHECK_PROGRESS" :   "학습 진도 체크를", "CHANGE_TIME" :   "시간 조정을", "TEACHER_COUNSELING" :   "담당 선생님 상담을"
}

answers_nollm = {
    "REASK"                         :   "죄송합니다. 질문을 이해하지 못했습니다. 이전 문의하신 내용을 계속 진행하시겠습니까?",
    "NEWASK"                        :   "안녕하세요! 웅진씽크빅 고객센터입니다. 어떤 도움이 필요하신가요? 다음 서비스를 제공해드릴 수 있습니다: \n 1.회원관련 2.교사채용 3.직원채용 4.고객 정보 업데이트",    
    "RECRUITMENT_TYPE"              :   "채용에 관련된 문의를 주셨네요. 우선 1) 씽크빅 선생님으로 입사하려는 건지요? 2) 웅진에 입사하려는 건지요?",
    "TEACHER_RECRUITMENT"           :   "네. 웅진씽크빅 상담교사에 대한 문의이시군요. 모집일정, 업무방식, 비전 등 문의내용을 좀 더 구체적으로 말씀해 주세요",
    "LEARNING_SUPPORT_ASK_USER"     :   "예. 자녀분 {} 원하시는 군요. \n 우선 자녀분 아이디나 학교/학년/이름을 말씀해 주실 수 있나요",
    "LEARNING_SUPPORT_WITH_USER"    :   "예. 자녀분 {} 원하시는 군요. 맞으실까요?",
    "CHECK_PROGRESS_CLASS"          :   "네. 고객님 자녀분 {student}은 {classes}수업을 듣고 계시네요. 둘 중 어느 수업 진도를 체크하고 싶으신가요?",
    "CHECK_PROGRESS_FANAL"          :   "네. 고객님 자녀분 {student}님은 {classes}에서 지난달엔 {class_last_month}을 마쳤고, 이번달엔 {class_now} 진행하고 있습니다. ... 해당 페이지 링크를 제공해 드릴까요?",
    "CHECK_PROGRESS_ADDTIONAL"      :   "네. 해당 주소는 https://m.wjthinkbig.com/prod/subjectDetail.do?subjectId=S0000059 입니다."
}

@app.post("/chat/")
async def chat(query: UserQuery):
    try:
        chain_type = "PROMPT"   # chain type : PROMPT/RAG/NO_LLM/DB (NO_LLM 빼곤 다 prompt정의됨.)
        # test_data = postrgre_db.fetch_all(db_sql.select_test, ("이웅진",))
        conv = conversation_state.get_conversation(query.conversation_id)
        # history = conversation_state.get_history_string(query.conversation_id)    # 이전 대화 내용 가져오기
        print(" -------------------------> query : ", query)
        print(" conv : ", conv)
        previous_intent = conv["intent"]        # 이전 의도 저장
        previous_step = conv["current_step"]    # 이전 단계 저장

        # 1. 의도 및 chain종류(RAG/PROMPT/NO_LLM/DB) 분류 #####################################################
        if not conv["intent"]:                  # 의도 분석 (새로운 대화이거나 분류 불가능한 이전 상태인 경우)
            intent = chain_intent["INTENT"].invoke({"question": query.question}).strip()
            # intent = intent_chain.invoke({"question": query.question}).strip() # 이렇게 그냥 프롬프트를 맞춰서 보내면 intent를 리턴해줌;;
            chain_type = "PROMPT"               # default는 PROMPT 이며 RAG나 DB만 처리함.
            dict_list = [chain_intent, chains_prompt, str_LEARNING_SUPPORT, answers_nollm]
            if intent in ["TEACHER_RECRUITMENT", "EMPLOYEE_RECRUITMENT", "LEARNING_SUPPORT"]:
            # if intent in (intent in d for d in dict_list):
                context = {                   # 프롬프트에 필요한 컨텍스트 구성
                        "question": query.question,
                        "current_step": conv["current_step"],
                        "context": json.dumps(conv["context"]),
                    } 
                # 채용 관련 의도 처리
                if intent in ["TEACHER_RECRUITMENT", "EMPLOYEE_RECRUITMENT"]:
                    if needs_recruitment_clarification(query.question):     # 선생님or직원 명확하지 않은 채용 문의인 경우
                        chain_type = "NO_LLM"         
                        answer = answers_nollm["RECRUITMENT_TYPE"]          # answer = "채용에 관련된 문의를 주셨네요. 우선 1) 씽크빅 선생님으로 입사하려는 건지요? 2) 웅진에 입사하려는 건지요?"                    
                        conv["intent"] = previous_intent                    # 이전 상태로 복원
                        conv["current_step"] = previous_step
                        conv["is_reset"] = False
                    else:
                        if conv["intent"] == "TEACHER_RECRUITMENT":         
                            if conv["current_step"] == "INITIAL":
                                chain_type = "NO_LLM"                                  
                                answer = answers_nollm["TEACHER_RECRUITMENT"]   # answer = "네. 웅진씽크빅 상담교사에 대한 문의이시군요. 모집일정, 업무방식, 비전 등 문의내용을 좀 더 구체적으로 말씀해 주세요"
                                conv["current_step"] = "INQUIRY"  
                            else:
                                chain_type = "RAG"     
                      # answer = (f"예. 자녀분 {str_LEARNING_SUPPORT[intent]} 원하시는 군요. 맞으실까요? ")
                elif intent in ["LEARNING_SUPPORT"]:                      # 한번 더 의도를 세분화 해서 파악 (LLM으로 vs 선생님or직원과 다른.. 이렇게 해야될듯..)
                    intent = chain_intent["INTENT_LEARNING_SUPPORT"].invoke(context).strip()  # 세부적인 의도 파악
                    conv["intent"] = intent
                else:
                    intent = "None"  
            
            # if not any(intent in d for d in dict_list):
            # all_keys = set(chain_intent.keys()) | set(chains_prompt.keys()) | set(str_LEARNING_SUPPORT.keys()) | set(answers_nollm.keys())
            if "None" in intent or not any(intent in d for d in dict_list):  # 분류 불가능한 경우 처리    
                chain_type = "NO_LLM"              
                if previous_intent:                                     # 이전 상태가 있었다면 그 상태 유지
                    # answer = "죄송합니다. 질문을 이해하지 못했습니다. 이전 문의하신 내용을 계속 진행하시겠습니까?"   
                    answer = answers_nollm["REASK"]                 
                    conv["intent"] = previous_intent                    # 이전 상태로 복원
                    conv["current_step"] = previous_step
                    conv["is_reset"] = False
                else:
                    # 완전히 새로운 대화인 경우
                    # answer = "안녕하세요! 웅진씽크빅 고객센터입니다. 어떤 도움이 필요하신가요? 다음 서비스를 제공해드릴 수 있습니다: \n 1.회원관련 2.교사채용 3.직원채용 4.고객 정보 업데이트"
                    answer = answers_nollm["NEWASK"]                                     
                    conv["intent"] = None
                    conv["current_step"] = None
                    conv["is_reset"] = True

            conv["intent"] = intent                     # 정상적인 의도 분류된 경우
            ######################################################## End


        
        if conv.get("intent", "") in ("CHECK_PROGRESS", "CHANGE_TIME", "TEACHER_COUNSELING"):
            # conv["intent"] = intent
            conv["is_reset"] = False
            if conv.get("intent", "") in ("CHECK_PROGRESS") :
                
                chat_history = memory.buffer_as_messages
                if conv["current_step"] == None :
                    conv["current_step"] = "FINAL"
                    response = agent_user_class_executor.invoke({
                        "input": query.question,
                        "chat_history": chat_history,
                    })
                else:
                    response = agent_progress_executor.invoke({
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
        # 2. 답변 생성 #########################################################
        if chain_type == "PROMPT":                      # chain type : PROMPT/RAG/NO_LLM/DB (NO_LLM 빼곤 다 prompt정의됨.)
            chain = chains_prompt[conv["intent"]]       # 현재 의도에 따른 프롬프트 체인 선택
            context = {                                 # 프롬프트에 필요한 컨텍스트 구성
                "question": query.question,
                "current_step": conv["current_step"],
                "context": json.dumps(conv["context"]),
                # "history": history
            }  
            answer = chain.invoke(context).strip()  # 응답 생성              
        elif chain_type == "NO_LLM":
            answer = answer.strip()
 # 에러 해결 요망 start ---------------->            
        # elif chain_type == "RAG":
        #     chain = chains_rag[conv["intent"]]          
        #     context = {                                     # 프롬프트에 필요한 컨텍스트 구성
        #         "question": query.question,
        #         "current_step": conv["current_step"],
        #         # "history": history
        #     } 
        #     # answer = chain.invoke(query.question).strip() # 같이 써도 될듯한데... 
        #     answer = chain.invoke(context).strip()  # 응답 생성
# 에러 해결 요망 end ----------------> 
        conversation_state.update_conversation( # 대화 이력 업데이트
            query.conversation_id,
            history=[{"question": query.question, "answer": answer, "step": conv["current_step"]}]
        )

        print(" chain_type : ", chain_type)        
        print(" answer ---- conv : ", conv)
        
        return {
            "answer": answer,
            "intent": conv["intent"],
            "current_step": conv["current_step"],
            "is_reset": conv["is_reset"], 
            "context": conv["context"]          # 현재 컨텍스트 상태도 반환
        }
        
    except Exception as e:
        print("error -----> ",  str(e))
        return {"error": str(e)}

def needs_recruitment_clarification(question: str) -> bool:
    """채용 문의가 명확한 구분이 필요한지 판단"""
    ambiguous_terms = [
        "지원", "채용", "입사", "취업", "일자리",
        "웅진", "씽크빅", "직장", "직무", "경력"
    ]
    
    specific_teacher_terms = ["선생님", "교사", "강사", "방문", "학습지"]
    specific_employee_terms = ["직원", "정직원", "사무직", "개발자", "편집"]
    
    # 일반적인 채용 관련 단어가 있으나
    has_ambiguous = any(term in question for term in ambiguous_terms)
    # 특정 직군을 명확히 지칭하는 단어가 없는 경우
    has_specific_teacher = any(term in question for term in specific_teacher_terms)
    has_specific_employee = any(term in question for term in specific_employee_terms)
    
    return has_ambiguous and not (has_specific_teacher or has_specific_employee)
    
