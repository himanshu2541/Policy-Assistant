# Makefile - development helpers for Policy Assistant Microservices
# Usage:
#   make dev-up            # bring up development compose (volumes + reload)
#   make prod-up           # bring up production compose (images baked in)
#   make restart SERVICE=chat  # restart single service container
#   make run SERVICE=chat      # run service locally (python -m ...)
#   make gen-protos        # generate grpc stubs (uses scripts/generate_protos.py)
#   make install-dev       # pip install -e shared & services in the active venv
#   make test              # run all pytest suites

SHELL := /bin/bash

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
	@echo "  make run SERVICE=<name>          -> run service locally with python -m (requires venv)"
	@echo "       Valid SERVICE names: gateway, chat, rag, worker, llm"
	@echo "  make docker-run SERVICE=<name>   -> docker compose run one-off service (for debug)"
	@echo "  make gen-protos    -> generate grpc python stubs (runs scripts/generate_protos.py)"
	@echo "  make install-dev   -> pip install -e ./shared and ./services/* in active venv"
	@echo "  make test          -> run all tests via pytest"

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

# Run service locally using python -m (requires venv + install-dev)
# Usage: make run SERVICE=chat
run:
ifndef SERVICE
	$(error SERVICE is not set. Example: make run SERVICE=chat)
endif
ifeq ($(SERVICE),gateway)
	@python -m services.api_gateway.api_gateway.cli
else ifeq ($(SERVICE),chat)
	@python -m services.chat_service.app.main
else ifeq ($(SERVICE),rag)
	@python -m services.rag_service.app.main
else ifeq ($(SERVICE),worker)
	@python -m services.rag_worker.rag_worker.cli
else ifeq ($(SERVICE),llm)
	@python -m services.llm_service.app.main
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
	@python scripts/generate_protos.py

install-dev:
	@echo "Installing editable packages into active venv..."
	@python -m pip install --upgrade pip setuptools wheel
	@python -m pip install -e ./shared || true
	@python -m pip install -e ./services/api_gateway || true
	@python -m pip install -e ./services/chat_service || true
	@python -m pip install -e ./services/rag_service || true
	@python -m pip install -e ./services/rag_worker || true
	@python -m pip install -e ./services/llm_service || true
	@echo "All services installed in editable mode."

test:
	@echo "Running all tests..."
	@python -m pytest services