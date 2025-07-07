# Docker 사용 가이드

## 빌드 및 실행

### 1. Docker 빌드
```bash
# 이미지 빌드
docker build -t m-asset-poc .

# 또는 Docker Compose 사용
docker compose build
```

### 2. 컨테이너 실행

#### 단일 컨테이너 실행
```bash
# 기본 실행 (bash 모드)
docker run -it --rm \
  -p 8010:8010 \
  -p 8011:8011 \
  -p 8888:8888 \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/logs:/app/logs \
  m-asset-poc

# 백그라운드 실행
docker run -d \
  --name m-asset-poc \
  -p 8010:8010 \
  -p 8011:8011 \
  -p 8888:8888 \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/logs:/app/logs \
  m-asset-poc
```

#### Docker Compose 실행
```bash
# 모든 서비스 시작
docker compose up -d

# 로그 확인
docker compose logs -f

# 특정 서비스만 시작
docker compose up -d m-asset-poc
```

## 서버 실행

### 컨테이너 접속 후 서버 실행
```bash
# 컨테이너 접속
docker exec -it m-asset-poc bash

# 개별 서버 실행
./start_api_server.sh      # API 서버 (포트 8010)
./start_a2a_server_new.sh  # A2A 서버 (포트 8011)
./start_jupyter.sh         # Jupyter Lab (포트 8888)

# 모든 서버 일괄 실행
./start_all_servers.sh

# 서버 중지
./stop_all_servers.sh
```

### 직접 명령어 실행
```bash
# API 서버
docker exec -d m-asset-poc python main.py --mode server

# A2A 서버
docker exec -d m-asset-poc python start_a2a_server.py

# Jupyter Lab
docker exec -d m-asset-poc jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root
```

## 포트 매핑

| 서비스 | 컨테이너 포트 | 호스트 접속 |
|--------|---------------|-------------|
| API 서버 | 8010 | http://localhost:8010 |
| A2A 서버 | 8011 | http://localhost:8011 |
| Jupyter Lab | 8888 | http://localhost:8888 |

## 환경 설정

### .env 파일 준비
컨테이너 실행 전에 `.env` 파일을 준비하세요:
```bash
# 예시 파일 복사
cp .env.example .env

# 필요한 환경 변수 수정
vim .env
```

### 주요 환경 변수
```bash
# 데이터베이스 (컨테이너 외부 DB 사용)
DB_HOST=host.docker.internal  # 호스트 머신의 DB 접속 시
DB_PORT=5432

# Redis (컨테이너 내부 Redis 사용)
REDIS_HOST=redis  # docker-compose 사용 시
REDIS_PORT=6379

# Weaviate (컨테이너 외부 Weaviate 사용)
WEAVIATE_HOST=host.docker.internal
WEAVIATE_PORT=8080
```

## 개발 모드

### 코드 변경사항 실시간 반영
```yaml
# docker-compose.yml에서 volumes 섹션 활성화
volumes:
  - ./src:/app/src  # 소스 코드 마운트
  - ./logs:/app/logs
  - ./.env:/app/.env
```

### 디버깅
```bash
# 컨테이너 내부 확인
docker exec -it m-asset-poc bash

# 로그 확인
docker compose logs -f m-asset-poc

# 프로세스 상태 확인
docker exec m-asset-poc ps aux

# 포트 사용 확인
docker exec m-asset-poc lsof -i :8010,8011,8888
```

## 문제 해결

### 1. 포트 충돌
```bash
# 호스트에서 포트 사용 확인
lsof -i :8010,8011,8888

# 다른 포트로 매핑
docker run -p 9010:8010 -p 9011:8011 -p 9888:8888 ...
```

### 2. 권한 문제
```bash
# 로그 디렉토리 권한 확인
chmod 755 logs/

# 스크립트 실행 권한
chmod +x start_*.sh stop_*.sh
```

### 3. 메모리 부족
```bash
# 리소스 제한 설정
docker run --memory="2g" --cpus="1.0" ...
```

### 4. 외부 서비스 연결
```bash
# 호스트 머신의 서비스 접속
# DB_HOST=host.docker.internal

# Docker 네트워크 내 서비스 접속
# REDIS_HOST=redis (docker-compose 사용 시)
```

## 운영 환경 배포

### 1. 프로덕션 빌드
```bash
# 최적화된 이미지 빌드
docker build --target production -t m-asset-poc:latest .

# 이미지 태그
docker tag m-asset-poc:latest your-registry/m-asset-poc:v1.0.0
```

### 2. 헬스체크 확인
```bash
# 컨테이너 헬스 상태 확인
docker ps --format "table {{.Names}}\t{{.Status}}"

# 수동 헬스체크
curl http://localhost:8010/health
curl http://localhost:8011/.well-known/agent.json
```

### 3. 로그 관리
```bash
# 로그 로테이션 설정
docker run --log-opt max-size=10m --log-opt max-file=3 ...

# 로그 수집
docker logs m-asset-poc > app.log 2>&1
```

## 정리

```bash
# 컨테이너 중지 및 제거
docker compose down

# 볼륨도 함께 제거
docker compose down -v

# 이미지 제거
docker rmi m-asset-poc

# 시스템 정리
docker system prune -a
```