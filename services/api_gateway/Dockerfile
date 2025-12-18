FROM python:3.11-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Install minimal OS deps used across services
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /ws/pyproject.toml

COPY shared ./shared
COPY shared/pyproject.toml /ws/shared/pyproject.toml

COPY services/api_gateway ./services/api_gateway
COPY services/api_gateway/pyproject.toml /ws/services/api_gateway/pyproject.toml

RUN --mount=type=bind,source=.,target=/ws \
    uv export --project /ws --frozen \
    --package shared \
    --format requirements-txt --no-emit-project \
    > /tmp/requirements_shared.txt

RUN --mount=type=bind,source=.,target=/ws \
    uv export --project /ws --frozen \
    --package api_gateway \
    --format requirements-txt --no-emit-project \
    > /tmp/requirements_service.txt

RUN uv pip install --system --no-cache-dir \
    -r /tmp/requirements_shared.txt \
    -r /tmp/requirements_service.txt

RUN uv pip install --system --no-deps ./shared
RUN uv pip install --system --no-deps ./services/api_gateway

EXPOSE 8000
CMD ["api-gateway"]
