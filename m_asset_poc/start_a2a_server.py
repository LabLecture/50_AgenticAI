#!/usr/bin/env python3
"""
A2A 서버 시작 스크립트
"""

import asyncio
import uvicorn
import os
import logging
from datetime import datetime
from src.a2a.text2sql_agent import Text2SQLAgent
from src.a2a.config import A2AConfig

def setup_logging():
    """로그 디렉토리 설정 및 로깅 구성"""
    # logs 디렉토리 생성
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # 현재 시간을 포함한 로그 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"a2a_server_{timestamp}.log")
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # 콘솔 출력도 유지
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"A2A 서버 로그가 {log_file}에 저장됩니다.")
    return log_file

def main():
    # 로깅 설정
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting A2A server on port 8011...")
        print(f"Starting A2A server on port 8011...")
        print(f"로그 파일: {log_file}")
        
        config = A2AConfig()
        agent = Text2SQLAgent(config)
        
        # FastAPI 앱 생성
        app = agent.create_fastapi_app()
        
        # uvicorn으로 서버 시작 (로그 파일 설정 포함)
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8011, 
            log_level="info",
            access_log=True,
            log_config={
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "default": {
                        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    },
                },
                "handlers": {
                    "default": {
                        "formatter": "default",
                        "class": "logging.StreamHandler",
                        "stream": "ext://sys.stdout",
                    },
                    "file": {
                        "formatter": "default",
                        "class": "logging.FileHandler",
                        "filename": log_file,
                        "encoding": "utf-8",
                    },
                },
                "root": {
                    "level": "INFO",
                    "handlers": ["default", "file"],
                },
            }
        )
        
    except Exception as e:
        logger.error(f"A2A 서버 시작 중 오류 발생: {e}")
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()