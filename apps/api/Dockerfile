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

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --upgrade pip && pip install .

COPY alembic.ini ./
COPY alembic ./alembic
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh && chown -R app:app /app

USER app
EXPOSE 8000

ARG GIT_SHA=unknown
ENV GIT_SHA=${GIT_SHA}

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "ksc_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
