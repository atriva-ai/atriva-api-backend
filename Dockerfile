FROM python:3.11-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

CMD ["/bin/sh", "-c", "python -m app.init_db && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
