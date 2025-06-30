# src/service/workflow_service.py
import logging
import json
from typing import Dict, List, Any

from src.config import TEAM_MEMBERS
from src.graph import build_graph
from langchain_community.adapters.openai import convert_message_to_dict
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def enable_debug_logging():
    """Enable debug level logging for more detailed execution information."""
    logging.getLogger("src").setLevel(logging.DEBUG)


logger = logging.getLogger(__name__)

# Create the graph
graph = build_graph()

async def run_agent_workflow(
    user_input_messages: list,
    debug: bool = False,
    deep_thinking_mode: bool = False,
    search_before_planning: bool = False,
):
    """Run the agent workflow with the given user input.

    Args:
        user_input_messages: The user request messages
        debug: If True, enables debug level logging
        deep_thinking_mode: Whether to use deep thinking mode
        search_before_planning: Whether to search before planning

    Returns:
        Dict containing the final response
    """
    if not user_input_messages:
        raise ValueError("Input could not be empty")
    
    if debug:
        enable_debug_logging()

    logger.info(f"Starting workflow with user input: {user_input_messages}")

    workflow_id = str(uuid.uuid4())
    
    # Instead of streaming, we'll execute the graph and wait for the complete output
    try:
        # Execute the graph and get the complete result

        result = await graph.ainvoke(
            {
                # Constants
                "TEAM_MEMBERS": TEAM_MEMBERS,
                # Runtime Variables
                "messages": user_input_messages,
                "deep_thinking_mode": deep_thinking_mode,
                "search_before_planning": search_before_planning,
            },
            # version="v2",
            config={"recursion_limit": 5}  # 재귀 제한을 5로 설정
        )
        
        logger.debug(f"Graph execution completed with result: {result}")
        
        # 마지막 AIMessage의 content를 answer로 추출
        answer = None
        for msg in reversed(result.get("messages", [])):
            if msg.__class__.__name__ == "AIMessage" and getattr(msg, "content", None):
                answer = msg.content
                break
        if not answer:
            answer = "No response generated."
        
        response = {
            "workflow_id": workflow_id,
            "input": user_input_messages,
            "answer": answer,
            "raw_result": result if debug else None
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error during graph execution: {e}", exc_info=True)
        return {
            "workflow_id": workflow_id,
            "input": user_input_messages,
            "answer": f"An error occurred: {str(e)}",
            "error": str(e)
        }