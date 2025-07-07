"""
A2A (Agent-to-Agent) Protocol integration for M-Asset Text2SQL Agent
"""

from .text2sql_agent import Text2SQLAgent
from .config import A2AConfig

__all__ = ["Text2SQLAgent", "A2AConfig"]