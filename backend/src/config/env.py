import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# [참고] 기존: REASONING_* / BASIC_* / VL_* 설정 → OpenRouter(OPENROUTER_API_KEY, OPENROUTER_MODEL)로 통일, src/agents/llm.py 참고
# # Reasoning LLM configuration (for complex reasoning tasks)
# REASONING_MODEL = os.getenv("REASONING_MODEL", "o1-mini")
# REASONING_BASE_URL = os.getenv("REASONING_BASE_URL")
# REASONING_API_KEY = os.getenv("REASONING_API_KEY")

# # Non-reasoning LLM configuration (for straightforward tasks)
# BASIC_MODEL = os.getenv("BASIC_MODEL", "gpt-4o")
# BASIC_BASE_URL = os.getenv("BASIC_BASE_URL")
# BASIC_API_KEY = os.getenv("BASIC_API_KEY")

# # Vision-language LLM configuration (for tasks requiring visual understanding)
# VL_MODEL = os.getenv("VL_MODEL", "gpt-4o")
# VL_BASE_URL = os.getenv("VL_BASE_URL")
# VL_API_KEY = os.getenv("VL_API_KEY")

# Chrome Instance configuration
CHROME_INSTANCE_PATH = os.getenv("CHROME_INSTANCE_PATH")
