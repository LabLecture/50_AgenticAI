#!/usr/bin/env python3
"""
Redis 직접 연결 테스트
"""
import redis
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# Redis 연결 테스트
print("=== Redis 연결 테스트 ===")

# 1. 비밀번호 있이 연결
try:
    client1 = redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        password="myredissecret",
        decode_responses=True
    )
    result1 = client1.ping()
    print(f"1. 비밀번호 'myredissecret'로 연결: 성공! PING={result1}")
except Exception as e:
    print(f"1. 비밀번호 'myredissecret'로 연결: 실패 - {e}")

# 2. 비밀번호 없이 연결
try:
    client2 = redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        password=None,
        decode_responses=True
    )
    result2 = client2.ping()
    print(f"2. 비밀번호 없이 연결: 성공! PING={result2}")
except Exception as e:
    print(f"2. 비밀번호 없이 연결: 실패 - {e}")

# 3. 빈 문자열 비밀번호로 연결
try:
    client3 = redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        password="",
        decode_responses=True
    )
    result3 = client3.ping()
    print(f"3. 빈 문자열 비밀번호로 연결: 성공! PING={result3}")
except Exception as e:
    print(f"3. 빈 문자열 비밀번호로 연결: 실패 - {e}")

# 4. os.getenv로 연결
password = os.getenv("REDIS_PASSWORD")
print(f"\n4. os.getenv('REDIS_PASSWORD') = '{password}'")
try:
    client4 = redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        password=password,
        decode_responses=True
    )
    result4 = client4.ping()
    print(f"   환경변수 비밀번호로 연결: 성공! PING={result4}")
except Exception as e:
    print(f"   환경변수 비밀번호로 연결: 실패 - {e}")