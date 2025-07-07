#!/usr/bin/env python3
"""
Redis 연결 디버깅
"""
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 환경 변수 직접 확인
print("=== 환경 변수 확인 ===")
print(f"REDIS_HOST: '{os.getenv('REDIS_HOST')}'")
print(f"REDIS_PORT: '{os.getenv('REDIS_PORT')}'")
print(f"REDIS_DB: '{os.getenv('REDIS_DB')}'")
print(f"REDIS_PASSWORD: '{os.getenv('REDIS_PASSWORD')}'")
print(f"LLM_CACHE_ENABLED: '{os.getenv('LLM_CACHE_ENABLED')}'")

# 빈 문자열 체크
password = os.getenv('REDIS_PASSWORD')
print(f"\n패스워드 길이: {len(password) if password else 0}")
print(f"패스워드가 빈 문자열인가? {password == ''}")
print(f"패스워드가 None인가? {password is None}")

# config 모듈 테스트
print("\n=== config 모듈 테스트 ===")
from src.core.config import config
print(f"config.get('REDIS_PASSWORD'): '{config.get('REDIS_PASSWORD')}'")
print(f"config.get('LLM_CACHE_ENABLED'): '{config.get('LLM_CACHE_ENABLED')}'")