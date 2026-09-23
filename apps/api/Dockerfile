# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --create-home --uid 1000 app

WORKDIR /app

COPY apps/api/pyproject.toml apps/api/README.md ./
COPY apps/api/src ./src
RUN pip install --upgrade pip \
 && pip install . \
 && pip uninstall -y pip

COPY apps/api/alembic.ini ./
COPY apps/api/alembic ./alembic
COPY apps/api/entrypoint.sh ./
COPY packages/prompts ./packages/prompts
RUN chmod +x entrypoint.sh && chown -R app:app /app

USER app
EXPOSE 8000

ARG GIT_SHA=unknown
ENV GIT_SHA=${GIT_SHA}

ENTRYPOINT ["./entrypoint.sh"]
# Access logging is the API's own structured JSON line (ksc_api.access).
CMD ["uvicorn", "ksc_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
