import os
import re
from datetime import datetime

from langchain_core.prompts import PromptTemplate
from langgraph.prebuilt.chat_agent_executor import AgentState

import logging
logger = logging.getLogger(__name__)

def get_prompt_template(prompt_name: str) -> str:
    # template = open(os.path.join(os.path.dirname(__file__), f"{prompt_name}.md")).read()
    template = open(os.path.join(os.path.dirname(__file__), f"{prompt_name}.md"), encoding='UTF-8').read()
    # Escape curly braces using backslash
    template = template.replace("{", "{{").replace("}", "}}")
    # Replace `<<VAR>>` with `{VAR}`
    template = re.sub(r"<<([^>>]+)>>", r"{\1}", template)
    return template


def apply_prompt_template(prompt_name: str, state: AgentState) -> list:
    template = get_prompt_template(prompt_name)
    logger.debug(f"Raw template apply_prompt_template {prompt_name}")
    system_prompt = PromptTemplate(
        input_variables=["CURRENT_TIME"],
        template=template,
    ).format(CURRENT_TIME=datetime.now().strftime("%a %b %d %Y %H:%M:%S %z"), **state)
    return [{"role": "system", "content": system_prompt}] + state["messages"]
