from typing import Literal

# Define available LLM types
LLMType = Literal["basic", "reasoning", "vision", "supervisor"]
# LLMType = Literal["basic", "reasoning", "vision"]

# Define agent-LLM mapping
AGENT_LLM_MAP: dict[str, LLMType] = {
    "coordinator"       : "basic",      # 
    "planner"           : "basic",  # 
    "supervisor"        : "supervisor",      # 
    "user_class"        : "basic",      # 
    "class_progress"    : "basic",      # 
}
