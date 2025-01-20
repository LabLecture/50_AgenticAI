from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from src.prompt import prompts
from dotenv import load_dotenv

from typing import Optional, Dict
import json

##########################
from langchain_core.tools import tool
from typing import Annotated
from langchain_core.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.memory import ConversationBufferMemory
from langchain.globals import set_verbose, set_debug
set_verbose(True)
set_debug(True)

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
llm = ChatOpenAI(
    model="gpt-4o",   #
    temperature=0.2,
    max_tokens=256,
    streaming=True
)

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


human = """
{input}

{agent_scratchpad}

(reminder to respond in a JSON blob no matter what)"""

    
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
        return "입력 정보에 부합되는 수업정보가 없습니다.  다시 자녀정보를 입력해주세요."
    
    # 수업 정보 포맷팅
    subjects = "\n".join([
        f"{i+1}. {item['subject_name']}\n"
        for i, item in enumerate(class_datas)
    ])
    return f"학생(자녀)이름:{user_name}\n학교:{user_school}\n학년:{user_grade}\n수업정보:\n{subjects}"
    


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
            입력 정보에 부합되는 수업정보가 없습니다.
            다시 입력해주세요.
        '''
        raise ValueError('해당 유저의 데이터가 존재하지 않습니다')
    
    return f'''
    학생(자녀)이름:{user_name}
    수업진도:{class_progress_data}
    '''
    
memory = ConversationBufferMemory(
    memory_key="chat_history",
    output_key="output",  # 출력 키 명시적 설정
    return_messages=True
)

agent_user_class = create_structured_chat_agent(
        llm, 
        [get_user_class_info],
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
    tools=[get_user_class_info],
    handle_parsing_errors=True,
    memory=memory,
    max_iterations=7,
)

agent_progress = create_structured_chat_agent(
        llm, 
        [get_user_class_progress_info],
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
    tools=[get_user_class_progress_info],
    handle_parsing_errors=True,
    memory=memory,
    max_iterations=7,
)

##########################
chain_intent = {        # 체인 정의 (중간 의도 파악용, 답변 활용X)
    "INTENT"                    :   prompts["intent_classifier_0"]                  | llm | StrOutputParser(),  # 기본 의도 파악
    "INTENT_LEARNING_SUPPORT"   :   prompts["intent_classifier_3_learning_support"] | llm | StrOutputParser(),  # 기본 의도 파악
    "INTENT_RECRUITMENT"        :   prompts["intent_classifier_23_recruitment"]     | llm | StrOutputParser()   # 교사or직원채용 의도파악용
}

chains_prompt = {
    "GREETING"              :   prompts["greeting_0"]               | llm | StrOutputParser(), # 단순인사 prompt
    "MEMBERSHIP"            :   prompts["membership_management_1"]  | llm | StrOutputParser(), 
    "LEARNING_SUPPORT"      :   prompts["learning_support"]         | llm | StrOutputParser(), 
    "TECHNICAL_SUPPORT"     :   prompts["technical_support"]        | llm | StrOutputParser(), 
    "GENERAL_INQUIRIES"     :   prompts["general_inquiries"]        | llm | StrOutputParser() 
}

str_LEARNING_SUPPORT = {
    "CHECK_PROGRESS" :   "학습 진도 체크를", "CHANGE_TIME" :   "시간 조정을", "TEACHER_COUNSELING" :   "담당 선생님 상담을"
}

answers_nollm = {
    "REASK"                 :   "죄송합니다. 질문을 이해하지 못했습니다. 이전 문의하신 내용을 계속 진행하시겠습니까?",
    "NEWASK"                :   "안녕하세요! 학습지 고객센터입니다. 어떤 도움이 필요하신가요? 다음 서비스를 제공해드릴 수 있습니다: \n 1.회원관련 2.교사채용 3.직원채용 4.고객 정보 업데이트"
}

@app.post("/chat/")
async def chat(query: UserQuery):
    try:
        conv = conversation_state.get_conversation(query.conversation_id)
        print(" conv : ", conv)
        previous_intent = conv["intent"]        # 이전 의도 저장
        previous_step = conv["current_step"]    # 이전 단계 저장
        answer = None                           # 일단 선언 먼저 필요.
        # 1. 의도 분류 #########################################################
        if not conv["intent"]:                  # 의도 분석 (새로운 대화이거나 분류 불가능한 이전 상태인 경우)
            intent = chain_intent["INTENT"].invoke({"question": query.question}).strip()
            
            
            dict_list = [chain_intent, chains_prompt, str_LEARNING_SUPPORT]
            if intent in ["TEACHER_RECRUITMENT", "EMPLOYEE_RECRUITMENT", "LEARNING_SUPPORT"]:
                context = {                   # 프롬프트에 필요한 컨텍스트 구성
                        "question": query.question,
                        "current_step": conv["current_step"],
                        "context": json.dumps(conv["context"]),
                    } 
                
                if intent in ["LEARNING_SUPPORT"]:                      # 한번 더 의도를 세분화 해서 파악 (LLM으로 vs 선생님or직원과 다른.. 이렇게 해야될듯..)
                    intent = chain_intent["INTENT_LEARNING_SUPPORT"].invoke(context).strip()  # 세부적인 의도 파악
                    conv["intent"] = intent
                else:
                    intent = "None"  

            if "None" in intent or not any(intent in d for d in dict_list):  # 분류 불가능한 경우 처리    
                if previous_intent:                                     # 이전 상태가 있었다면 그 상태 유지
                    answer = answers_nollm["REASK"]                 
                    conv["intent"] = previous_intent                    # 이전 상태로 복원
                    conv["current_step"] = previous_step
                    conv["is_reset"] = False
                else:
                    # answer = "안녕하세요! 웅진씽크빅 고객센터입니다. 어떤 도움이 필요하신가요? 다음 서비스를 제공해드릴 수 있습니다: \n 1.회원관련 2.교사채용 3.직원채용 4.고객 정보 업데이트"
                    answer = answers_nollm["NEWASK"]                                     
                    conv["intent"] = None
                    conv["current_step"] = None
                    conv["is_reset"] = True

            conv["intent"] = intent                     # 정상적인 의도 분류된 경우

        # 2. 답변 생성 #########################################################
        if conv.get("intent", "") in ("CHECK_PROGRESS", "CHANGE_TIME", "TEACHER_COUNSELING"):
            conv["is_reset"] = False
            if conv.get("intent", "") in ("CHECK_PROGRESS") :
                
                chat_history = memory.buffer_as_messages
                if conv["current_step"] == None :
                    response = agent_user_class_executor.invoke({
                        "input": query.question,
                        "chat_history": chat_history,
                    })
                    if "수업 진도를 체크하고 싶으신가요" in response['output']:   
                        conv["current_step"] = "FINAL"      # 수업정보가 있으면 준비 OK 라서 다음 FINAL로 update

                else:
                    response = agent_progress_executor.invoke({
                        "input": query.question,
                        "chat_history": chat_history,
                    })
                    if "더 필요한 사항은 있으실까요? 학습안내" in response['output']:   # intent 초기화 ################# prompt에 intent 종료 시그널 포함시켜야 됨.
                        conv["current_step"] = None
                        conv["intent"] = ""     
                print(response)
            
                answer = response['output']     

        answer = answer.strip()
        conversation_state.update_conversation( # 대화 이력 업데이트
            query.conversation_id,
            history=[{"question": query.question, "answer": answer, "step": conv["current_step"]}]
        )

        return {
            "answer": answer,
            "intent": conv["intent"],
            "current_step": conv["current_step"],
            "is_reset": conv["is_reset"], 
            "context": conv["context"]          # 현재 컨텍스트 상태도 반환
        }            
        

        
    except Exception as e:
        print(e)
        return {"error": str(e)}
    
