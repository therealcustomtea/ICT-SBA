# syntax=docker/dockerfile:1.7@sha256:a57df69d0ea827fb7266491f2813635de6f17269be881f696fbfdf2d83dda33e
# Pins the base image used for this reproducible container stage.
FROM python:3.13.14-slim-bookworm@sha256:9d7f287598e1a5a978c015ee176d8216435aaf335ed69ac3c38dd1bbb10e8d64 AS builder

# Defines the environment used by subsequent container instructions.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

# Sets the working directory for the container instructions that follow.
WORKDIR /build

# Runs the command required to prepare or start this container stage.
RUN python -m pip install --no-cache-dir uv==0.11.23

# Copies only the required build input into the container image.
COPY pyproject.toml uv.lock ./
# Copies only the required build input into the container image.
COPY apps/api ./apps/api
# Copies only the required build input into the container image.
COPY apps/cli ./apps/cli
# Copies only the required build input into the container image.
COPY packages/mastermind_core ./packages/mastermind_core

# Runs the command required to prepare or start this container stage.
RUN uv sync --frozen --no-dev --no-editable

# Pins the base image used for this reproducible container stage.
FROM python:3.13.14-slim-bookworm@sha256:9d7f287598e1a5a978c015ee176d8216435aaf335ed69ac3c38dd1bbb10e8d64 AS runtime

# Defines the environment used by subsequent container instructions.
ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MASTERMIND_ENVIRONMENT=production

# Runs the command required to prepare or start this container stage.
RUN groupadd --system --gid 10001 mastermind \
    && useradd --system --uid 10001 --gid mastermind --home-dir /app mastermind

# Sets the working directory for the container instructions that follow.
WORKDIR /app

# Copies only the required build input into the container image.
COPY --from=builder --chown=mastermind:mastermind /opt/venv /opt/venv
# Drops privileges by selecting the runtime user for later instructions.
USER 10001:10001

# Documents the network port served by the container.
EXPOSE 8000

# Defines the probe used to determine whether the container is healthy.
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)"]

# Performs this required step in the script or container workflow.
STOPSIGNAL SIGTERM

# Runs the command required to prepare or start this container stage.
CMD ["uvicorn", "mastermind_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--no-server-header"]
