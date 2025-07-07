# 서버 운영 가이드

## 개요

M-Asset POC는 두 개의 주요 서버로 구성됩니다:
- **API 서버** (포트 8010): 내부 테스트 및 REST API 제공
- **A2A 서버** (포트 8011): Agent-to-Agent 통신을 위한 주 인터페이스

## 서버 시작

### 1. 빠른 시작 (권장)

모든 서버를 백그라운드로 한 번에 시작:

```bash
./start_all_servers.sh
```

이 스크립트는 다음 작업을 자동으로 수행합니다:
- 가상환경 활성화
- .env 파일 확인
- 기존 프로세스 정리
- Redis/Weaviate 상태 확인
- API 서버와 A2A 서버 시작
- PID 파일 생성

### 2. 개별 서버 시작

**API 서버만 시작:**
```bash
./start_api_server.sh
```

**A2A 서버만 시작:**
```bash
./start_a2a_server_new.sh
```

### 3. 수동 시작

**API 서버:**
```bash
source venv/bin/activate
python main.py --mode server
```

**A2A 서버:**
```bash
source venv/bin/activate
python start_a2a_server.py
```

## 서버 중지

### 모든 서버 중지

```bash
./stop_all_servers.sh
```

### 수동 중지

```bash
# PID 확인
lsof -ti:8010  # API 서버
lsof -ti:8011  # A2A 서버

# 프로세스 종료
kill -TERM <PID>
```

## 프로세스 모니터링

### 1. 서버 상태 확인

**API 서버 상태:**
```bash
curl http://localhost:8010/health
curl http://localhost:8010/status
```

**A2A 서버 상태:**
```bash
curl http://localhost:8011/.well-known/agent.json
```

### 2. 프로세스 확인

```bash
# 실행 중인 서버 확인
ps aux | grep -E "main.py|start_a2a_server.py"

# 포트 사용 확인
lsof -i :8010,8011
```

### 3. PID 파일 확인

```bash
# API 서버 PID
cat .api_server.pid

# A2A 서버 PID
cat .a2a_server.pid
```

## 로그 관리

### 로그 파일 위치

- **API 서버**: `logs/api_server.log`
- **A2A 서버**: `logs/a2a_server_YYYYMMDD_HHMMSS.log`

### 실시간 로그 모니터링

```bash
# API 서버 로그
tail -f logs/api_server.log

# A2A 서버 로그 (최신 파일)
tail -f logs/a2a_server_*.log

# 모든 로그 동시 모니터링
tail -f logs/*.log
```

### 로그 검색

```bash
# 에러 검색
grep -i error logs/*.log

# 특정 날짜 로그
ls logs/a2a_server_20250630_*.log

# 특정 키워드 검색
grep "query" logs/api_server.log
```

## 트러블슈팅

### 1. 서버가 시작되지 않을 때

**포트 충돌 확인:**
```bash
# 포트 사용 중인 프로세스 확인
lsof -i :8010
lsof -i :8011

# 강제 종료
kill -9 $(lsof -ti:8010)
kill -9 $(lsof -ti:8011)
```

**환경 변수 확인:**
```bash
# .env 파일 존재 확인
ls -la .env

# 필수 환경 변수 확인
grep -E "DB_|VLLM_|API_" .env
```

### 2. Redis 연결 오류

```bash
# Redis 상태 확인
redis-cli ping

# Redis 시작 (macOS)
brew services start redis

# Redis 시작 (Linux)
sudo systemctl start redis
```

### 3. Weaviate 연결 오류

```bash
# Weaviate 상태 확인
curl http://localhost:8080/v1/.well-known/ready

# 벡터 스토어 비활성화 (.env)
WEAVIATE_ENABLED=false
```

### 4. 메모리 부족

```bash
# 메모리 사용량 확인
ps aux | grep python | awk '{sum+=$6} END {print sum/1024 " MB"}'

# 서버 재시작
./stop_all_servers.sh
./start_all_servers.sh
```

## 성능 모니터링

### 동시성 상태

```bash
# API 서버 동시성
curl http://localhost:8010/concurrency/status

# A2A 서버 동시성
curl http://localhost:8011/concurrency/status
```

### 캐시 상태

```bash
# 캐시 통계
curl http://localhost:8010/cache/stats

# 캐시 초기화
curl -X POST http://localhost:8010/cache/clear
```

### 연결 풀 상태

```bash
# Weaviate 연결 풀
curl http://localhost:8010/vector-store/pool/stats
```

## 백업 및 복구

### 로그 백업

```bash
# 로그 디렉토리 백업
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/

# 오래된 로그 정리
find logs/ -name "*.log" -mtime +30 -delete
```

### Redis 캐시 백업

```bash
# Redis 데이터 저장
redis-cli BGSAVE

# dump.rdb 파일 백업
cp dump.rdb dump_backup_$(date +%Y%m%d).rdb
```

## 보안 고려사항

1. **방화벽 설정**: 프로덕션 환경에서는 8010, 8011 포트 접근 제한
2. **HTTPS 설정**: 리버스 프록시(nginx)를 통한 SSL 적용
3. **환경 변수 보호**: .env 파일 권한 설정 (chmod 600)
4. **로그 보안**: 민감한 정보가 로그에 포함되지 않도록 주의

## 자동화 스크립트

### systemd 서비스 (Linux)

`/etc/systemd/system/m-asset-api.service`:
```ini
[Unit]
Description=M-Asset API Server
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/path/to/m_asset_poc
Environment="PATH=/path/to/m_asset_poc/venv/bin"
ExecStart=/path/to/m_asset_poc/venv/bin/python main.py --mode server
Restart=always

[Install]
WantedBy=multi-user.target
```

### cron 작업 (로그 정리)

```bash
# 매일 오전 3시에 30일 이상된 로그 삭제
0 3 * * * find /path/to/m_asset_poc/logs -name "*.log" -mtime +30 -delete
```

## 모범 사례

1. **정기적인 재시작**: 메모리 누수 방지를 위해 주기적으로 서버 재시작
2. **로그 모니터링**: 에러 패턴을 주기적으로 확인
3. **백업 정책**: 로그와 캐시 데이터 정기 백업
4. **리소스 모니터링**: CPU, 메모리 사용량 추적
5. **버전 관리**: 배포 전 태그 생성 및 롤백 계획 수립