# syntax=docker/dockerfile:1.7@sha256:a57df69d0ea827fb7266491f2813635de6f17269be881f696fbfdf2d83dda33e
FROM python:3.13.14-slim-bookworm@sha256:9d7f287598e1a5a978c015ee176d8216435aaf335ed69ac3c38dd1bbb10e8d64 AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /build

RUN python -m pip install --no-cache-dir uv==0.11.23

COPY pyproject.toml uv.lock ./
COPY apps/api ./apps/api
COPY apps/cli ./apps/cli
COPY packages/mastermind_core ./packages/mastermind_core

RUN uv sync --frozen --no-dev --no-editable

FROM python:3.13.14-slim-bookworm@sha256:9d7f287598e1a5a978c015ee176d8216435aaf335ed69ac3c38dd1bbb10e8d64 AS runtime

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MASTERMIND_ENVIRONMENT=production

RUN groupadd --system --gid 10001 mastermind \
    && useradd --system --uid 10001 --gid mastermind --home-dir /app mastermind

WORKDIR /app

COPY --from=builder --chown=mastermind:mastermind /opt/venv /opt/venv
COPY --from=builder --chown=mastermind:mastermind /build/apps/api/alembic /app/apps/api/alembic
COPY --from=builder --chown=mastermind:mastermind /build/apps/api/alembic.ini /app/apps/api/alembic.ini

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)"]

STOPSIGNAL SIGTERM

CMD ["uvicorn", "mastermind_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--no-server-header"]
