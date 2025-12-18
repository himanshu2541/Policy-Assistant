FROM python:3.11-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    ffmpeg \
    libsndfile1 \
    libgomp1 \
    libopenblas-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /ws/pyproject.toml

COPY shared ./shared
COPY shared/pyproject.toml /ws/shared/pyproject.toml

COPY services/rag_worker ./services/rag_worker
COPY services/rag_worker/pyproject.toml /ws/services/rag_worker/pyproject.toml

RUN --mount=type=bind,source=.,target=/ws \
    uv export --project /ws --frozen \
    --package shared \
    --format requirements-txt --no-emit-project \
    > /tmp/requirements_shared.txt

RUN --mount=type=bind,source=.,target=/ws \
    uv export --project /ws --frozen \
    --package rag_worker \
    --format requirements-txt --no-emit-project \
    > /tmp/requirements_service.txt

# Install dependencies, allow best-match across indexes so torch can come from the cpu index
RUN uv pip install --system --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    --index-strategy=unsafe-best-match \
    -r /tmp/requirements_shared.txt \
    -r /tmp/requirements_service.txt

COPY shared ./shared
RUN uv pip install --system --no-deps ./shared

COPY services/rag_worker ./services/rag_worker
RUN uv pip install --system --no-deps ./services/rag_worker

CMD ["rag-worker"]
