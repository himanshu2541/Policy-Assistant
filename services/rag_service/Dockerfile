FROM python:3.11-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# RAG service uses vector libs / redis clients; include general native deps
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

COPY services/rag_service ./services/rag_service
COPY services/rag_service/pyproject.toml /ws/services/rag_service/pyproject.toml

RUN --mount=type=bind,source=.,target=/ws \
    uv export --project /ws --frozen \
    --package shared \
    --format requirements-txt --no-emit-project \
    > /tmp/requirements_shared.txt

RUN --mount=type=bind,source=.,target=/ws \
    uv export --project /ws --frozen \
    --package rag_service \
    --format requirements-txt --no-emit-project \
    > /tmp/requirements_service.txt

RUN uv pip install --system --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    --index-strategy=unsafe-best-match \
    -r /tmp/requirements_shared.txt \
    -r /tmp/requirements_service.txt

RUN uv pip install --system --no-deps ./shared
RUN uv pip install --system --no-deps ./services/rag_service

EXPOSE 50052
CMD ["rag-service"]
