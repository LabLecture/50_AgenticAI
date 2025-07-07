"""
Logging configuration module for M-Asset POC.
Sets up console and file logging with different levels.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    console_output: bool = True,
    file_output: bool = True
) -> logging.Logger:
    """
    개발 단계용 로깅 설정
    
    Args:
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 로그 파일 저장 디렉토리
        console_output: 콘솔 출력 여부
        file_output: 파일 출력 여부
    
    Returns:
        설정된 로거 인스턴스
    """
    
    # 로그 디렉토리 생성
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # 로그 레벨 설정
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # 기본 로거 설정
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # 기존 핸들러 제거 (중복 방지)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 로그 포맷 설정
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 콘솔 핸들러 (색상 포함)
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
    
    # 파일 핸들러들
    if file_output:
        # 1. 일반 로그 파일 (INFO 이상)
        app_handler = logging.FileHandler(
            log_path / "app.log", 
            mode='a',
            encoding='utf-8'
        )
        app_handler.setLevel(logging.INFO)
        app_handler.setFormatter(detailed_formatter)
        logger.addHandler(app_handler)
        
        # 2. 에러 로그 파일 (ERROR 이상)
        error_handler = logging.FileHandler(
            log_path / "error.log",
            mode='a', 
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)
        
        # 3. 디버그 로그 파일 (DEBUG 레벨일 때만)
        if level <= logging.DEBUG:
            debug_handler = logging.FileHandler(
                log_path / "debug.log",
                mode='a',
                encoding='utf-8'
            )
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.setFormatter(detailed_formatter)
            logger.addHandler(debug_handler)
    
    return logger


def setup_uvicorn_logging(log_level: str = "INFO") -> dict:
    """
    Uvicorn 서버용 로깅 설정
    
    Args:
        log_level: 로그 레벨
        
    Returns:
        Uvicorn 로그 설정 딕셔너리
    """
    
    log_path = Path("logs")
    log_path.mkdir(exist_ok=True)
    
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "access": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(client_addr)s - %(request_line)s - %(status_code)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "formatter": "default",
                "class": "logging.FileHandler",
                "filename": str(log_path / "uvicorn.log"),
                "mode": "a",
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["default", "file"],
                "level": log_level.upper(),
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["default", "file"],
                "level": log_level.upper(),
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["access", "file"],
                "level": log_level.upper(),
                "propagate": False,
            },
        },
    }


def get_logger(name: str) -> logging.Logger:
    """
    모듈별 로거 생성
    
    Args:
        name: 로거 이름 (보통 __name__ 사용)
        
    Returns:
        로거 인스턴스
    """
    return logging.getLogger(name)


# 환경 변수에서 로그 설정 읽기
def get_log_config_from_env() -> dict:
    """환경 변수에서 로그 설정 읽기"""
    return {
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "log_dir": os.getenv("LOG_DIR", "logs"),
        "console_output": os.getenv("LOG_CONSOLE", "true").lower() == "true",
        "file_output": os.getenv("LOG_FILE", "true").lower() == "true",
    }