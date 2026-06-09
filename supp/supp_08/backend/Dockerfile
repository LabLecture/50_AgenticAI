# [6교시] 백엔드 컨테이너 — uvicorn 으로 FastAPI 실행
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
# 컨테이너 안에서는 0.0.0.0 으로 바인딩해야 외부에서 접속 가능
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
