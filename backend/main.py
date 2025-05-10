from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from typing import Optional, Dict
import json

load_dotenv()
app = FastAPI()

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
    question: str
    conversation_id: Optional[str] = None
    current_step: Optional[str] = None


import logging
from src.config import TEAM_MEMBERS
from src.graph import build_graph
# Create the graph
graph = build_graph()

# Configure logging
logger = logging.getLogger("03_langmanus/geon_woonjin")
logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',level=logging.DEBUG,datefmt='%m/%d/%Y %I:%M:%S',
)

def run_agent_workflow(user_input: str, debug: bool = False):
    """Run the agent workflow with the given user input.

    Args:
        user_input: The user's query or request
        debug: If True, enables debug level logging

    Returns:
        The final state after the workflow completes
    """
    if not user_input:
        raise ValueError("Input could not be empty")

    if debug:
        enable_debug_logging()

    logger.info(f"Starting workflow with user input: {user_input}")
    result = graph.invoke(
        {
            # Constants
            "TEAM_MEMBERS": TEAM_MEMBERS,
            # Runtime Variables
            "messages": [{"role": "user", "content": user_input}],
            "deep_thinking_mode": True,
            "search_before_planning": False,
        }
    )
    logger.debug(f"Final workflow state: {result}")
    logger.info("Workflow completed successfully")
    return result
  
@app.post("/chat/")
async def chat(query: UserQuery):
    try:
        # answer = run_agent_workflow(query.question).strip() 
        result = run_agent_workflow(query.question)

        messages = result.get("messages", [])
        last_message = messages[-1] if messages else None
        answer_text = last_message.content if last_message and hasattr(last_message, "content") else "응답이 없습니다."

        print(" --------> answer_text : ", answer_text)
        return {
            "answer": answer_text,
            # "intent": conv["intent"],
            # "current_step": conv["current_step"],
            # "is_reset": conv["is_reset"], 
            # "context": conv["context"]          # 현재 컨텍스트 상태도 반환
        }            
        
    except Exception as e:
        print(e)
        return {"error": str(e)}
    
