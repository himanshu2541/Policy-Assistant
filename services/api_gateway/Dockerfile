FROM python:3.11-slim AS build

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY pyproject.toml ./pyproject.toml
COPY services/api_gateway ./services/api_gateway
COPY shared ./shared

RUN python -m pip install --upgrade pip setuptools wheel \
    && pip wheel ./shared ./services/api_gateway -w /wheels \
    && pip install --no-cache-dir /wheels/*

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN addgroup --system app && adduser --system --ingroup app app
WORKDIR /app

COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build /usr/local/bin /usr/local/bin

COPY services/api_gateway /app/services/api_gateway
COPY shared /app/shared

USER app
EXPOSE 8000
CMD ["api-gateway"]