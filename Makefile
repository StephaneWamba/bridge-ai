.PHONY: help up down logs build restart shell-backend shell-frontend migrate test lint format

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## View logs from all services
	docker-compose logs -f

build: ## Build all Docker images
	docker-compose build

restart: ## Restart all services
	docker-compose restart

shell-backend: ## Open shell in backend container
	docker-compose exec backend /bin/bash

shell-frontend: ## Open shell in frontend container
	docker-compose exec frontend /bin/sh

migrate: ## Run database migrations
	docker-compose exec backend alembic upgrade head

migrate-create: ## Create new migration (usage: make migrate-create MESSAGE="migration name")
	docker-compose exec backend alembic revision --autogenerate -m "$(MESSAGE)"

test: ## Run tests
	docker-compose exec backend pytest

lint-backend: ## Lint backend code
	docker-compose exec backend ruff check .
	docker-compose exec backend mypy src/

lint-frontend: ## Lint frontend code
	docker-compose exec frontend pnpm lint
	docker-compose exec frontend pnpm type-check

format-backend: ## Format backend code
	docker-compose exec backend ruff format .

format-frontend: ## Format frontend code
	docker-compose exec frontend pnpm format

clean: ## Remove all containers and volumes
	docker-compose down -v

