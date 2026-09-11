FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/backend

RUN groupadd --system terrasync \
    && useradd --system --gid terrasync --home /app terrasync

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend/ /app/backend/
COPY field_app/ /app/field_app/
COPY coordinator_dashboard/ /app/coordinator_dashboard/
COPY supervisor_dashboard/ /app/supervisor_dashboard/
COPY dashboard/ /app/dashboard/

RUN chown -R terrasync:terrasync /app

USER terrasync

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=3)"

CMD ["sh", "-c", "if [ \"${TRUSTED_PROXY_HEADERS:-false}\" = \"true\" ]; then exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log --proxy-headers --forwarded-allow-ips=\"${FORWARDED_ALLOW_IPS:-127.0.0.1}\"; else exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log; fi"]
