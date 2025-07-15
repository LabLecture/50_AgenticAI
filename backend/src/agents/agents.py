from langgraph.prebuilt import create_react_agent

from src.prompts import apply_prompt_template
from src.tools import (
    user_class_tool,
    class_progress_tool,
    link_provider_tool,
)

from .llm import get_llm_by_type
from src.config.agents import AGENT_LLM_MAP

# Create agents using configured LLM types  agent는 하나만 쓰는게 맞는 거 같은데.. 일단 나눴음.
import logging

logger = logging.getLogger(__name__)

# Create agents using configured LLM types
def create_user_class_agent():
    llm = get_llm_by_type(AGENT_LLM_MAP["user_class"])
    tools = [user_class_tool]
    
    logger.info(f"Creating_apply_prompt_template_수행전 ")

    prompt = lambda state: apply_prompt_template("user_class", state)
    
    logger.info(f"Creating_user_class_agent with tools: {tools}")
    logger.info(f"user_class_agent_prompt template: {prompt}")
    
    agent = create_react_agent(
        llm,
        name="user_class",
        tools=tools,
        prompt=prompt,
    )
    return agent

def create_class_progress_agent():
    llm = get_llm_by_type(AGENT_LLM_MAP["class_progress"])
    tools = [class_progress_tool]
    prompt = lambda state: apply_prompt_template("class_progress", state)
    
    logger.info(f"Creating_class_progress_agent with tools: {tools}")
    logger.info(f"class_progress_agent prompt template: {prompt}")
    
    agent = create_react_agent(
        llm,
        name="class_progress",
        tools=tools,
        prompt=prompt,
    )
    return agent

def create_link_provider_agent():
    llm = get_llm_by_type(AGENT_LLM_MAP["link_provider"])
    tools = [link_provider_tool]
    prompt = lambda state: apply_prompt_template("link_provider", state)
    
    logger.info(f"Creating_link_provider_agent with tools: {tools}")
    logger.info(f"link_provider_agent_prompt template: {prompt}")
    
    agent = create_react_agent(
        llm,
        name="link_provider",
        tools=tools,
        prompt=prompt,
    )
    return agent

user_class_agent = create_user_class_agent()
class_progress_agent = create_class_progress_agent()
link_provider_agent = create_link_provider_agent()
