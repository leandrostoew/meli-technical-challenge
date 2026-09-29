FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

RUN pip install --no-cache-dir --root-user-action=ignore "scapy==2.7.0"

COPY src /app/src

ENTRYPOINT ["python", "-m", "traffic_analyzer"]
