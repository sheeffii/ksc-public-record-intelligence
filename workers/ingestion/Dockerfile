# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN useradd --create-home --uid 1000 worker
WORKDIR /app

COPY apps/api /app/apps/api
COPY workers/ingestion /app/workers/ingestion
COPY packages/prompts /app/packages/prompts
RUN pip install --upgrade pip \
 && pip install /app/apps/api /app/workers/ingestion \
 && pip uninstall -y pip \
 && chown -R worker:worker /app

USER worker
ENTRYPOINT ["ksc-ingest"]
CMD ["status"]
