# Makefile - development helpers for microservices-endpoints
# Usage:
#   make dev-up            # bring up development compose (volumes + reload)
#   make prod-up           # bring up production compose (images baked in)
#   make restart SERVICE=query  # restart single service container
#   make run SERVICE=query      # run service locally (python -m ...)
#   make gen-protos         # generate grpc stubs (uses scripts/gen_protos.py)
#   make install-dev        # pip install -e shared & services in the active venv
#   make test               # run test_all_connections.py

SHELL := /bin/bash

# Files
DEV_COMPOSE := docker-compose.dev.yml
PROD_COMPOSE := docker-compose.yml

# Default docker-compose command, allow override (eg: DOCKER_COMPOSE=docker compose)
DOCKER_COMPOSE ?= docker compose

.PHONY: help dev-up dev-down dev-build dev-logs \
        prod-up prod-down prod-build prod-logs \
        up down build logs \
        restart build-service run docker-run \
        gen-protos install-dev test python-run

help:
	@echo "Makefile targets:"
	@echo "  make dev-up         -> docker compose up for development (uses $(DEV_COMPOSE))"
	@echo "  make dev-down       -> docker compose down for development"
	@echo "  make dev-build      -> docker compose build for development"
	@echo "  make dev-logs       -> follow logs for development"
	@echo "  make prod-up        -> docker compose up for production (uses $(PROD_COMPOSE))"
	@echo "  make prod-down      -> docker compose down for production"
	@echo "  make prod-build     -> docker compose build for production"
	@echo "  make prod-logs      -> follow logs for production"
	@echo "  make restart SERVICE=<name>       -> restart single service container (by compose service name)"
	@echo "  make build-service SERVICE=<name> -> build single service image"
	@echo "  make run SERVICE=<name>           -> run service locally with python -m (requires venv)"
	@echo "  make docker-run SERVICE=<name>    -> docker compose run one-off service (for debug)"
	@echo "  make gen-protos    -> generate grpc python stubs (runs scripts/gen_protos.py)"
	@echo "  make install-dev   -> pip install -e ./shared and ./services/* in active venv"
	@echo "  make test          -> run test_all_connections.py (ensure venv has deps)"

### Development targets (volumes, reload)
dev-up:
	@$(DOCKER_COMPOSE) -f $(DEV_COMPOSE) up --build

dev-down:
	@$(DOCKER_COMPOSE) -f $(DEV_COMPOSE) down

dev-build:
	@$(DOCKER_COMPOSE) -f $(DEV_COMPOSE) build

dev-logs:
	@$(DOCKER_COMPOSE) -f $(DEV_COMPOSE) logs -f

### Production targets (baked images)
prod-up:
	@$(DOCKER_COMPOSE) -f $(PROD_COMPOSE) up --build -d

prod-down:
	@$(DOCKER_COMPOSE) -f $(PROD_COMPOSE) down

prod-build:
	@$(DOCKER_COMPOSE) -f $(PROD_COMPOSE) build

prod-logs:
	@$(DOCKER_COMPOSE) -f $(PROD_COMPOSE) logs -f

### Single-service helpers
# Usage: make restart SERVICE=query
restart:
ifndef SERVICE
	$(error SERVICE is not set. Example: make restart SERVICE=query)
endif
	@$(DOCKER_COMPOSE) restart $(SERVICE)

# Usage: make build-service SERVICE=stt
build-service:
ifndef SERVICE
	$(error SERVICE is not set. Example: make build-service SERVICE=stt)
endif
	@$(DOCKER_COMPOSE) build $(SERVICE)

# Run service locally using python -m (requires venv + uv sync / editable installs)
# SERVICE values: query, ingest, stt  (maps below)
python-run:
ifndef SERVICE
	$(error SERVICE is not set. Example: make python-run SERVICE=query)
endif
ifeq ($(SERVICE),query)
	@python -m services.query_service.cli
else ifeq ($(SERVICE),ingest)
	@python -m services.ingestion_service.cli
else ifeq ($(SERVICE),stt)
	@python -m services.stt_service.cli
else
	$(error Unknown SERVICE '$(SERVICE)'. Valid: query, ingest, stt)
endif

# Run service in a one-off docker container (helpful to debug entrypoint)
# Usage: make docker-run SERVICE=query
docker-run:
ifndef SERVICE
	$(error SERVICE is not set. Example: make docker-run SERVICE=query)
endif
	@$(DOCKER_COMPOSE) run --rm --service-ports $(SERVICE)

### Developer utilities
gen-protos:
	@python scripts/gen_protos.py

install-dev:
	@echo "Installing editable packages into active venv..."
	@python -m pip install --upgrade pip setuptools wheel
	@python -m pip install -e ./shared || true
	@python -m pip install -e ./services/query_service || true
	@python -m pip install -e ./services/ingestion_service || true
	@python -m pip install -e ./services/stt_service || true
	@echo "Done."

test:
	@python test_all_connections.py
