"""
A2A standalone server for Text2SQL Agent
A2A 프로토콜만을 위한 독립형 서버
"""

import asyncio
import logging
from typing import Optional

from ..core.config import config
from .text2sql_agent import Text2SQLAgent

logger = logging.getLogger(__name__)

class A2AStandaloneServer:
    """A2A 독립형 서버"""
    
    def __init__(self):
        self.agent: Optional[Text2SQLAgent] = None
        
    async def initialize(self):
        """서버 초기화"""
        if not config.a2a.enabled:
            raise ValueError("A2A is not enabled in configuration")
        
        try:
            self.agent = Text2SQLAgent(config.a2a)
            if not self.agent.is_available():
                raise ValueError("A2A agent is not available")
            
            logger.info("A2A standalone server initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize A2A standalone server: {e}")
            raise
    
    async def start(self, host: str = "0.0.0.0", port: int = 8011):
        """서버 시작"""
        if not self.agent:
            await self.initialize()
        
        logger.info(f"Starting A2A standalone server on {host}:{port}")
        logger.info(f"Agent Card available at: http://{host}:{port}/.well-known/agent.json")
        
        try:
            await self.agent.start_server(host=host, port=port)
        except Exception as e:
            logger.error(f"Error starting A2A server: {e}")
            raise

async def main():
    """메인 함수"""
    server = A2AStandaloneServer()
    
    try:
        await server.start(
            host=config.a2a.base_url.split("://")[1].split(":")[0] if "://" in config.a2a.base_url else "0.0.0.0",
            port=int(config.a2a.base_url.split(":")[-1]) if ":" in config.a2a.base_url else 8011
        )
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())