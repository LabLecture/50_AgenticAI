# M-Asset POC Dockerfile
# Python 3.10 기반 멀티 스테이지 빌드

# Build stage
FROM python:3.10-slim as builder

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치를 위한 pip 업그레이드
RUN pip install --upgrade pip

# 작업 디렉토리 설정
WORKDIR /app

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.10-slim as production

# 시스템 의존성 설치 (런타임만)
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    vim \
    htop \
    lsof \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 빌드 스테이지에서 Python 패키지 복사
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 애플리케이션 코드 복사
COPY . .

# 로그 디렉토리 생성
RUN mkdir -p logs

# 스크립트 실행 권한 부여
RUN chmod +x start_*.sh stop_*.sh

# 포트 노출 (API: 8010, A2A: 8011, Jupyter: 8888)
EXPOSE 8010 8011 8888

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 헬스체크 추가 (선택적 - API 또는 A2A 서버 중 하나라도 동작하면 OK)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8010/health 2>/dev/null || \
        curl -f http://localhost:8011/.well-known/agent.json 2>/dev/null || \
        exit 1

# 기본 명령어를 bash로 설정 (수동 실행 가능)
CMD ["/bin/bash"]