#!/bin/bash

# 모든 서버 시작 스크립트 (백그라운드)
# 사용법: ./start_all_servers.sh

echo "🚀 M-Asset 모든 서버를 시작합니다..."

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
    echo "⚠️  .env 파일이 없습니다."
    exit 1
fi

# logs 디렉토리 생성
mkdir -p logs

# 기존 프로세스 종료 함수
stop_process_on_port() {
    local PORT=$1
    local NAME=$2
    local PID=$(lsof -ti:$PORT 2>/dev/null)
    
    if [ ! -z "$PID" ]; then
        echo "🛑 포트 $PORT에서 실행 중인 $NAME 프로세스를 종료합니다 (PID: $PID)..."
        kill -TERM $PID 2>/dev/null
        sleep 2
        
        if kill -0 $PID 2>/dev/null; then
            kill -KILL $PID 2>/dev/null
        fi
        echo "✅ $NAME 프로세스를 종료했습니다."
    fi
}

# 기존 프로세스 모두 종료
echo "🔍 기존 프로세스를 확인합니다..."
stop_process_on_port 8010 "API 서버"
stop_process_on_port 8011 "A2A 서버"

# Redis 상태 확인
if grep -q "LLM_CACHE_ENABLED=true" .env; then
    echo "🔍 Redis 서버 상태를 확인합니다..."
    if command -v redis-cli &> /dev/null && redis-cli ping &> /dev/null; then
        echo "✅ Redis 서버가 실행 중입니다."
    else
        echo "⚠️  Redis 서버가 실행되지 않았습니다."
    fi
fi

# API 서버 시작 (백그라운드)
echo "🌐 API 서버를 시작합니다 (포트: 8010)..."
nohup python main.py --mode server > logs/api_server.log 2>&1 &
API_PID=$!
echo "✅ API 서버가 시작되었습니다. (PID: $API_PID)"

# API 서버가 준비될 때까지 대기
sleep 3

# A2A 서버 시작 (백그라운드)
echo "🌐 A2A 서버를 시작합니다 (포트: 8011)..."
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
A2A_LOG="logs/a2a_server_${TIMESTAMP}.log"
nohup python start_a2a_server.py > "$A2A_LOG" 2>&1 &
A2A_PID=$!
echo "✅ A2A 서버가 시작되었습니다. (PID: $A2A_PID)"

# 프로세스 ID를 파일에 저장
echo "$API_PID" > .api_server.pid
echo "$A2A_PID" > .a2a_server.pid

echo ""
echo "✅ 모든 서버가 시작되었습니다!"
echo ""
echo "📊 서버 상태 확인:"
echo "  - API 서버: http://localhost:8010/health"
echo "  - A2A 서버: http://localhost:8011/.well-known/agent.json"
echo ""
echo "📝 로그 확인:"
echo "  - API 서버: tail -f logs/api_server.log"
echo "  - A2A 서버: tail -f $A2A_LOG"
echo ""
echo "🛑 서버 중지: ./stop_all_servers.sh"