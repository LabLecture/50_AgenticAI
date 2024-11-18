# syntax=docker/dockerfile:1
FROM python:3.10

# install app dependencies
WORKDIR /app

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /app/
RUN target=/root/.cache/pip \
    pip3 install -r requirements.txt

# Copy the entire project into the working directory
# COPY . /app
COPY .env.* ./
# final configuration
EXPOSE 8000
# CMD ["fastapi", "run", "main.py"]
# 직접 실행하지 않고 컨테이너만 유지
CMD ["tail", "-f", "/dev/null"]     