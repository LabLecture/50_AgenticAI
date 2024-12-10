FROM python:3.10
  
WORKDIR /app

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /app/

# pip 설치 시 타임아웃 및 재시도 설정 추가
# RUN pip config set global.timeout 1000 \
#     && pip config set global.retries 5 \
#     && pip install --upgrade pip \
#     && pip install --no-cache-dir \
#        --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
#        --trusted-host pypi.tuna.tsinghua.edu.cn \
#        -r requirements.txt
RUN pip install -r requirements.txt

COPY .env.* ./

# final configuration
EXPOSE 8000
CMD ["tail", "-f", "/dev/null"]