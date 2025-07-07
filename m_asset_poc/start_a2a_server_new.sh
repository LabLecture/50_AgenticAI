#!/bin/bash

# A2A 서버 시작 스크립트
# 사용법: ./start_a2a_server_new.sh

echo "🚀 M-Asset A2A 서버를 시작합니다..."

# 스크립트가 있는 디렉토리로 이동
cd "$(dirname "$0")"

# 가상환경 활성화
if [ -d "venv" ]; then
    echo "✅ 가상환경을 활성화합니다..."
    source venv/bin/activate
else
    echo "❌ 가상환경을 찾을 수 없습니다. venv 디렉토리를 확인하세요."
    exit 1
fi

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다. .env.example을 참고하여 생성하세요."
    if [ -f ".env.example" ]; then
        echo "💡 cp .env.example .env 명령으로 복사할 수 있습니다."
    fi
    exit 1
fi

# 기존 A2A 서버 프로세스 확인 및 종료
echo "🔍 기존 A2A 서버 프로세스를 확인합니다..."
A2A_PID=$(lsof -ti:8011 2>/dev/null)

if [ ! -z "$A2A_PID" ]; then
    echo "⚠️  포트 8011에서 실행 중인 프로세스를 발견했습니다 (PID: $A2A_PID)"
    echo "🛑 기존 프로세스를 종료합니다..."
    kill -TERM $A2A_PID 2>/dev/null
    sleep 2
    
    # 프로세스가 여전히 실행 중이면 강제 종료
    if kill -0 $A2A_PID 2>/dev/null; then
        echo "⚠️  프로세스가 정상 종료되지 않아 강제 종료합니다..."
        kill -KILL $A2A_PID 2>/dev/null
    fi
    echo "✅ 기존 프로세스를 종료했습니다."
fi

# Redis 상태 확인 (캐싱이 활성화된 경우)
if grep -q "LLM_CACHE_ENABLED=true" .env; then
    echo "🔍 Redis 서버 상태를 확인합니다..."
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null; then
            echo "✅ Redis 서버가 실행 중입니다."
        else
            echo "⚠️  Redis 서버가 실행되지 않았습니다. LLM 캐싱이 작동하지 않을 수 있습니다."
        fi
    fi
fi

# Weaviate 상태 확인 (활성화된 경우)
if grep -q "WEAVIATE_ENABLED=true" .env; then
    echo "🔍 Weaviate 서버 상태를 확인합니다..."
    WEAVIATE_HOST=$(grep "WEAVIATE_HOST=" .env | cut -d'=' -f2)
    WEAVIATE_PORT=$(grep "WEAVIATE_PORT=" .env | cut -d'=' -f2)
    if curl -s "http://${WEAVIATE_HOST}:${WEAVIATE_PORT}/v1/.well-known/ready" > /dev/null 2>&1; then
        echo "✅ Weaviate 서버가 실행 중입니다."
    else
        echo "⚠️  Weaviate 서버에 연결할 수 없습니다. 벡터 검색이 작동하지 않을 수 있습니다."
    fi
fi

# A2A 서버 시작
echo "🌐 A2A 서버를 시작합니다 (포트: 8011)..."
echo "📝 로그는 logs/ 디렉토리에 타임스탬프와 함께 저장됩니다."
echo "⏹️  중지하려면 Ctrl+C를 누르세요."
echo "-" * 50

# logs 디렉토리 생성
mkdir -p logs

# 백그라운드로 실행하려면 아래 주석을 해제하세요
# TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
# LOG_FILE="logs/a2a_server_${TIMESTAMP}.log"
# nohup python start_a2a_server.py > "$LOG_FILE" 2>&1 &
# echo "✅ A2A 서버가 백그라운드에서 시작되었습니다. (PID: $!)"
# echo "📝 로그 확인: tail -f $LOG_FILE"

# 포그라운드 실행 (기본)
python start_a2a_server.py