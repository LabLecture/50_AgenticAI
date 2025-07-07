#!/bin/bash

# Jupyter Lab 시작 스크립트
# 사용법: ./start_jupyter.sh

echo "🚀 Jupyter Lab을 시작합니다..."

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

# Jupyter Lab 실행
echo "🌐 Jupyter Lab을 시작합니다..."
echo "📝 브라우저가 자동으로 열립니다."
echo "⏹️  중지하려면 Ctrl+C를 누르세요."
echo "-" * 50

# Jupyter Lab 실행 (포트 8888, 브라우저 자동 열기)
jupyter lab --port=8888 --no-browser --ip=0.0.0.0