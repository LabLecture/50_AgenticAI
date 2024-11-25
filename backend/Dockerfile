FROM python:3.10
  
WORKDIR /app

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /app/

RUN pip install -r requirements.txt

COPY .env.* ./

# final configuration
EXPOSE 8000
CMD ["tail", "-f", "/dev/null"]
