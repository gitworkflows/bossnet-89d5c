# Makefile for Bangladesh Education Data API

# Variables
PROJECT_NAME := bangladesh-education-data
PYTHON := python
PIP := pip
DOCKER := docker
DOCKER_COMPOSE := docker-compose
PYTEST := pytest
ALEMBIC := alembic

# Default target
.DEFAULT_GOAL := help

# Help target to show available commands
.PHONY: help
help:  ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development

install:  ## Install development dependencies
	$(PIP) install -e .[dev]
	$(PIP) install -r requirements.txt

format:  ## Format code with Black and isort
	black .
	isort .

lint:  ## Lint code with flake8 and mypy
	flake8
	mypy .

test:  ## Run tests
	$(PYTEST) --cov=src --cov-report=term-missing

##@ Database

db-up:  ## Start database containers
	$(DOCKER_COMPOSE) up -d db redis

db-down:  ## Stop database containers
	$(DOCKER_COMPOSE) stop db redis

db-shell:  ## Connect to the database with psql
	$(DOCKER_COMPOSE) exec db psql -U postgres -d student_data_db

migrate:  ## Run database migrations
	$(ALEMBIC) upgrade head

migrate-create:  ## Create a new migration
	@read -p "Enter migration message: " message; \
	$(ALEMBIC) revision --autogenerate -m "$$message"

##@ Docker

docker-build:  ## Build Docker image
	$(DOCKER_COMPOSE) build

docker-up:  ## Start all services in detached mode
	$(DOCKER_COMPOSE) up -d

docker-down:  ## Stop all services
	$(DOCKER_COMPOSE) down

docker-logs:  ## View logs from all services
	$(DOCKER_COMPOSE) logs -f

docker-clean:  ## Remove all containers, networks, and volumes
	$(DOCKER_COMPOSE) down -v
	$(DOCKER) system prune -f

##@ Application

run:  ## Run the application locally
	uvicorn src.main:app --reload

shell:  ## Open a Python shell with the application context
	python -m IPython

##@ Documentation

docs-serve:  ## Serve documentation locally
	mkdocs serve

docs-build:  ## Build documentation
	mkdocs build

##@ Cleanup

clean:  ## Clean up temporary files
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
	rm -rf .coverage htmlcov/ build/ dist/ *.egg-info/

.PHONY: help install format lint test db-up db-down db-shell migrate migrate-create docker-build docker-up docker-down docker-logs docker-clean run shell docs-serve docs-build clean
