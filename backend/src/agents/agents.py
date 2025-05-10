from langgraph.prebuilt import create_react_agent

from src.prompts import apply_prompt_template
from src.tools import (
    user_class_tool,
    class_progress_tool,
)

from .llm import get_llm_by_type
from src.config.agents import AGENT_LLM_MAP

# Create agents using configured LLM types  agent는 하나만 쓰는게 맞는 거 같은데.. 일단 나눴음.
user_class_agent = create_react_agent(
    get_llm_by_type(AGENT_LLM_MAP["user_class"]),
    name="user_class",
    tools=[user_class_tool],
    prompt=lambda state: apply_prompt_template("user_class", state),
)

class_progress_agent = create_react_agent(
    get_llm_by_type(AGENT_LLM_MAP["class_progress"]),
    name="class_progress",
    tools=[class_progress_tool],
    prompt=lambda state: apply_prompt_template("class_progress", state),
)