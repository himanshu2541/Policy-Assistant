FROM python:3.11-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

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

COPY services/llm_service ./services/llm_service
COPY services/llm_service/pyproject.toml /ws/services/llm_service/pyproject.toml

RUN --mount=type=bind,source=.,target=/ws \
    uv export --project /ws --frozen \
    --package shared \
    --format requirements-txt --no-emit-project \
    > /tmp/requirements_shared.txt

RUN --mount=type=bind,source=.,target=/ws \
    uv export --project /ws --frozen \
    --package llm_service \
    --format requirements-txt --no-emit-project \
    > /tmp/requirements_service.txt

RUN uv pip install --system --no-cache-dir \
    -r /tmp/requirements_shared.txt \
    -r /tmp/requirements_service.txt

RUN uv pip install --system --no-deps ./shared
RUN uv pip install --system --no-deps ./services/llm_service

EXPOSE 50053
CMD ["llm-service"]
