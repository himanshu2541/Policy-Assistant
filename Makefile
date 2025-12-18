# Makefile - development helpers for Policy Assistant Microservices
# Usage:
#   make dev-up            # bring up development compose (volumes + reload)
#   make prod-up           # bring up production compose (images baked in)
#   make restart SERVICE=chat  # restart single service container
#   make run SERVICE=chat      # run service locally using uv (uv run ...)
#   make gen-protos        # generate grpc stubs (uses scripts/generate_protos.py)
#   make install-dev       # sync uv workspace (installs all services in editable mode)
#   make test              # run all pytest suites

SHELL := /bin/bash

# Enable BuildKit for Docker (Required for the new Dockerfiles)
export DOCKER_BUILDKIT=1

# Files
DEV_COMPOSE := docker-compose.dev.yml
PROD_COMPOSE := docker-compose.yml

# Default docker-compose command, allow override (eg: DOCKER_COMPOSE=docker compose)
DOCKER_COMPOSE ?= docker compose

.PHONY: help dev-up dev-down dev-build dev-logs \
        prod-up prod-down prod-build prod-logs \
        up down build logs \
        restart build-service python-run docker-run \
        gen-protos install-dev test

help:
	@echo "Makefile targets:"
	@echo "  make dev-up        -> docker compose up for development (uses $(DEV_COMPOSE))"
	@echo "  make dev-down      -> docker compose down for development"
	@echo "  make dev-build     -> docker compose build for development"
	@echo "  make dev-logs      -> follow logs for development"
	@echo "  make prod-up       -> docker compose up for production (uses $(PROD_COMPOSE))"
	@echo "  make prod-down     -> docker compose down for production"
	@echo "  make prod-build    -> docker compose build for production"
	@echo "  make prod-logs     -> follow logs for production"
	@echo "  make restart SERVICE=<name>      -> restart single service container (by compose service name)"
	@echo "  make build-service SERVICE=<name> -> build single service image"
	@echo "  make run SERVICE=<name>          -> run service locally using 'uv run' (uses project.scripts)"
	@echo "       Valid SERVICE names: gateway, chat, rag, worker, llm"
	@echo "  make docker-run SERVICE=<name>   -> docker compose run one-off service (for debug)"
	@echo "  make gen-protos    -> generate grpc python stubs (runs scripts/generate_protos.py)"
	@echo "  make install-dev   -> run 'uv sync' to install workspace in editable mode"
	@echo "  make test          -> run all tests via pytest"

### Development targets (volumes, reload)
dev-up:
	@$(DOCKER_COMPOSE) -f $(DEV_COMPOSE) up

dev-down:
	@$(DOCKER_COMPOSE) -f $(DEV_COMPOSE) down

dev-build:
	@$(DOCKER_COMPOSE) -f $(DEV_COMPOSE) build

dev-logs:
	@$(DOCKER_COMPOSE) -f $(DEV_COMPOSE) logs -f

### Production targets (baked images)
prod-up:
	@$(DOCKER_COMPOSE) -f $(PROD_COMPOSE) up -d

prod-down:
	@$(DOCKER_COMPOSE) -f $(PROD_COMPOSE) down

prod-build:
	@$(DOCKER_COMPOSE) -f $(PROD_COMPOSE) build

prod-logs:
	@$(DOCKER_COMPOSE) -f $(PROD_COMPOSE) logs -f

### Single-service helpers
# Usage: make restart SERVICE=chat_service
restart:
ifndef SERVICE
	$(error SERVICE is not set. Example: make restart SERVICE=chat_service)
endif
	@$(DOCKER_COMPOSE) restart $(SERVICE)

# Usage: make build-service SERVICE=rag_service
build-service:
ifndef SERVICE
	$(error SERVICE is not set. Example: make build-service SERVICE=rag_service)
endif
	@$(DOCKER_COMPOSE) build $(SERVICE)

# Run service locally using uv run (uses the entry points defined in pyproject.toml)
# Usage: make run SERVICE=chat
run:
ifndef SERVICE
	$(error SERVICE is not set. Example: make run SERVICE=chat)
endif
ifeq ($(SERVICE),gateway)
	@uv run api-gateway
else ifeq ($(SERVICE),chat)
	@uv run chat-service
else ifeq ($(SERVICE),rag)
	@uv run rag-service
else ifeq ($(SERVICE),worker)
	@uv run rag-worker
else ifeq ($(SERVICE),llm)
	@uv run llm-service
else
	$(error Unknown SERVICE '$(SERVICE)'. Valid: gateway, chat, rag, worker, llm)
endif

# Run service in a one-off docker container (helpful to debug entrypoint)
# Usage: make docker-run SERVICE=chat_service
docker-run:
ifndef SERVICE
	$(error SERVICE is not set. Example: make docker-run SERVICE=chat_service)
endif
	@$(DOCKER_COMPOSE) run --rm --service-ports $(SERVICE)

### Developer utilities
gen-protos:
	@uv run python scripts/generate_protos.py

install-dev:
	@echo "Syncing uv workspace..."
	@uv sync
	@echo "Workspace synced. All services installed in editable mode."

test:
	@echo "Running all tests..."
	@uv run pytest services