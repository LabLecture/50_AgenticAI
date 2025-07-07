"""
A2A (Agent-to-Agent) Protocol configuration
"""

from pydantic import BaseModel, Field
from typing import Optional

class A2AConfig(BaseModel):
    """A2A 프로토콜 설정"""
    
    enabled: bool = Field(default=False, env="A2A_ENABLED")
    base_url: str = Field(default="http://localhost:8010", env="A2A_BASE_URL")
    auth_token: Optional[str] = Field(default=None, env="A2A_AUTH_TOKEN")
    
    # Agent Card 정보
    agent_name: str = Field(default="M-Asset Text2SQL Agent", env="A2A_AGENT_NAME")
    agent_description: str = Field(
        default="한국 증권 데이터에 대한 자연어 질의를 SQL로 변환하고 실행하는 에이전트", 
        env="A2A_AGENT_DESCRIPTION"
    )
    agent_version: str = Field(default="1.0.0", env="A2A_AGENT_VERSION")
    
    # 기능 설정
    streaming_enabled: bool = Field(default=True, env="A2A_STREAMING_ENABLED")
    push_notifications_enabled: bool = Field(default=False, env="A2A_PUSH_NOTIFICATIONS_ENABLED")
    state_history_enabled: bool = Field(default=True, env="A2A_STATE_HISTORY_ENABLED")
    
    class Config:
        env_file = ".env"