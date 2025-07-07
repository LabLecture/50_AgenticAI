#!/bin/bash

# 모든 서버 중지 스크립트
# 사용법: ./stop_all_servers.sh

echo "🛑 M-Asset 모든 서버를 중지합니다..."

# 스크립트가 있는 디렉토리로 이동
cd "$(dirname "$0")"

# 프로세스 종료 함수
stop_process() {
    local PID_FILE=$1
    local NAME=$2
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 $PID 2>/dev/null; then
            echo "🛑 $NAME을 중지합니다 (PID: $PID)..."
            kill -TERM $PID 2>/dev/null
            sleep 2
            
            if kill -0 $PID 2>/dev/null; then
                echo "⚠️  정상 종료되지 않아 강제 종료합니다..."
                kill -KILL $PID 2>/dev/null
            fi
            echo "✅ $NAME을 중지했습니다."
        else
            echo "ℹ️  $NAME이 이미 중지되어 있습니다."
        fi
        rm -f "$PID_FILE"
    fi
}

# 포트로 프로세스 종료 (백업)
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

# PID 파일로 프로세스 종료
stop_process ".api_server.pid" "API 서버"
stop_process ".a2a_server.pid" "A2A 서버"

# 포트로도 확인 (PID 파일이 없을 경우를 대비)
stop_process_on_port 8010 "API 서버"
stop_process_on_port 8011 "A2A 서버"

echo ""
echo "✅ 모든 서버가 중지되었습니다."