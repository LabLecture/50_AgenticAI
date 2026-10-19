from .env import (
    # [참고] 기존 REASONING_* / BASIC_* / VL_* 는 OpenRouter 로 통일하며 제거
    # Other configurations
    CHROME_INSTANCE_PATH,
)
from .tools import TAVILY_MAX_RESULTS

# Team configuration
TEAM_MEMBERS = ["user_class", "class_progress"]
# TEAM_MEMBERS = ["researcher", "coder", "browser", "reporter"]

__all__ = [
    # [참고] 기존 REASONING_* / BASIC_* / VL_* 는 OpenRouter 로 통일하며 제거
    # Other configurations
    "TEAM_MEMBERS",
    "TAVILY_MAX_RESULTS",
    "CHROME_INSTANCE_PATH",
]
