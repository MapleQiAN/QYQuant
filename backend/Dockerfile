FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

RUN apt-get update -o Acquire::Retries=5 -o Acquire::http::Timeout=30 \
    && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
COPY packages/qysp ./packages/qysp

RUN pip install --no-cache-dir -r backend/requirements.txt \
    && pip install --no-cache-dir ./packages/qysp

FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update -o Acquire::Retries=5 -o Acquire::http::Timeout=30 \
    && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local /usr/local

COPY backend ./backend

WORKDIR /app/backend

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

CMD ["sh", "-lc", "flask --app app db upgrade && gunicorn --bind 0.0.0.0:5000 --workers ${GUNICORN_WORKERS:-4} --timeout ${GUNICORN_TIMEOUT:-120} --access-logfile - --error-logfile - 'app:create_app()'"]
