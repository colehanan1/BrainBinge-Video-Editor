# HeyGen Social Clipper - Makefile
# Build, test, and development automation

.PHONY: help install install-dev test lint format coverage clean run docs build deploy

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := pip3
PYTEST := pytest
VENV := venv
SRC_DIR := src
TEST_DIR := tests
DOCS_DIR := docs

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ General

help: ## Display this help message
	@echo "$(BLUE)HeyGen Social Clipper - Build Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(GREEN)<target>$(NC)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup & Installation

install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install -e .
	@echo "$(GREEN)Installation complete!$(NC)"

install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install -e ".[dev]"
	@echo "$(GREEN)Development installation complete!$(NC)"

venv: ## Create virtual environment
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	$(PYTHON) -m venv $(VENV)
	@echo "$(GREEN)Virtual environment created!$(NC)"
	@echo "$(YELLOW)Activate with: source $(VENV)/bin/activate$(NC)"

setup: venv install-dev ## Complete development setup (venv + install)
	@echo "$(GREEN)Development environment ready!$(NC)"

##@ Code Quality

lint: ## Run code linting (flake8)
	@echo "$(BLUE)Running linter...$(NC)"
	@# Will be implemented after code is added
	@# flake8 $(SRC_DIR) $(TEST_DIR) --max-line-length=100
	@echo "$(YELLOW)Linting not yet configured (no code implemented)$(NC)"

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	@# Will be implemented after code is added
	@# black $(SRC_DIR) $(TEST_DIR)
	@# isort $(SRC_DIR) $(TEST_DIR)
	@echo "$(YELLOW)Formatting not yet configured (no code implemented)$(NC)"

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checker...$(NC)"
	@# Will be implemented after code is added
	@# mypy $(SRC_DIR)
	@echo "$(YELLOW)Type checking not yet configured (no code implemented)$(NC)"

check: lint type-check ## Run all code quality checks
	@echo "$(GREEN)All checks complete!$(NC)"

##@ Testing

test: ## Run unit tests
	@echo "$(BLUE)Running tests...$(NC)"
	@# Will be implemented after tests are added
	@# $(PYTEST) $(TEST_DIR) -v
	@echo "$(YELLOW)Tests not yet implemented$(NC)"

test-fast: ## Run tests excluding slow tests
	@echo "$(BLUE)Running fast tests...$(NC)"
	@# $(PYTEST) $(TEST_DIR) -v -m "not slow"
	@echo "$(YELLOW)Tests not yet implemented$(NC)"

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	@# $(PYTEST) $(TEST_DIR) -v -m "integration"
	@echo "$(YELLOW)Tests not yet implemented$(NC)"

coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@# $(PYTEST) $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term
	@# @echo "$(GREEN)Coverage report generated in htmlcov/index.html$(NC)"
	@echo "$(YELLOW)Coverage not yet configured (no tests implemented)$(NC)"

##@ Development

run: ## Run CLI tool (example command)
	@echo "$(BLUE)Running heygen-clipper...$(NC)"
	heygen-clipper --help

run-webhook: ## Start webhook server (development)
	@echo "$(BLUE)Starting webhook server...$(NC)"
	@# heygen-clipper webhook --host localhost --port 8000 --config config/brand.yaml --output-dir output/
	@echo "$(YELLOW)Webhook server requires implementation$(NC)"

watch: ## Watch for file changes and run tests
	@echo "$(BLUE)Watching for changes...$(NC)"
	@# $(PYTEST) $(TEST_DIR) -f
	@echo "$(YELLOW)Watch mode not yet configured$(NC)"

##@ Documentation

docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	@# Will be implemented if Sphinx is added
	@# cd $(DOCS_DIR) && make html
	@echo "$(YELLOW)Documentation generation not yet configured$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(NC)"
	@# cd $(DOCS_DIR)/_build/html && python -m http.server 8080
	@echo "$(YELLOW)Documentation not yet available$(NC)"

##@ Building & Packaging

build: clean ## Build distribution packages
	@echo "$(BLUE)Building distribution packages...$(NC)"
	$(PYTHON) setup.py sdist bdist_wheel
	@echo "$(GREEN)Build complete! Packages in dist/$(NC)"

validate: ## Validate package build
	@echo "$(BLUE)Validating package...$(NC)"
	twine check dist/*
	@echo "$(GREEN)Package validation complete!$(NC)"

##@ Cleaning

clean: ## Remove build artifacts and cache files
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf $(SRC_DIR)/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type f -name '*~' -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .tox/
	@echo "$(GREEN)Cleanup complete!$(NC)"

clean-data: ## Clean temporary and output data (CAREFUL!)
	@echo "$(RED)WARNING: This will delete all temporary and output files!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf data/temp/*; \
		rm -rf data/output/*; \
		echo "$(GREEN)Data cleaned!$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled.$(NC)"; \
	fi

clean-all: clean clean-data ## Remove all build artifacts and data

##@ Deployment

deploy-test: ## Deploy to test PyPI
	@echo "$(BLUE)Deploying to Test PyPI...$(NC)"
	twine upload --repository testpypi dist/*
	@echo "$(GREEN)Deployed to Test PyPI!$(NC)"

deploy-prod: ## Deploy to production PyPI
	@echo "$(RED)Deploying to Production PyPI...$(NC)"
	@read -p "Are you sure you want to deploy to production? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		twine upload dist/*; \
		echo "$(GREEN)Deployed to PyPI!$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled.$(NC)"; \
	fi

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t heygen-clipper:latest .
	@echo "$(GREEN)Docker image built!$(NC)"

docker-run: ## Run Docker container
	@echo "$(BLUE)Running Docker container...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Container running!$(NC)"

docker-stop: ## Stop Docker container
	@echo "$(BLUE)Stopping Docker container...$(NC)"
	docker-compose down
	@echo "$(GREEN)Container stopped!$(NC)"

##@ Utilities

version: ## Show version information
	@echo "$(BLUE)Version Information:$(NC)"
	@echo "Python: $$($(PYTHON) --version)"
	@echo "pip: $$($(PIP) --version)"
	@echo "FFmpeg: $$(ffmpeg -version | head -n1)"

env-check: ## Check environment setup
	@echo "$(BLUE)Environment Check:$(NC)"
	@command -v python3 >/dev/null 2>&1 && echo "$(GREEN)✓$(NC) Python 3 installed" || echo "$(RED)✗$(NC) Python 3 not found"
	@command -v ffmpeg >/dev/null 2>&1 && echo "$(GREEN)✓$(NC) FFmpeg installed" || echo "$(RED)✗$(NC) FFmpeg not found"
	@command -v git >/dev/null 2>&1 && echo "$(GREEN)✓$(NC) Git installed" || echo "$(RED)✗$(NC) Git not found"
	@[ -f .env ] && echo "$(GREEN)✓$(NC) .env file exists" || echo "$(YELLOW)⚠$(NC) .env file not found (copy from .env.example)"

init-config: ## Initialize configuration files from examples
	@echo "$(BLUE)Initializing configuration...$(NC)"
	@[ ! -f .env ] && cp .env.example .env && echo "$(GREEN)Created .env$(NC)" || echo "$(YELLOW).env already exists$(NC)"
	@mkdir -p config data/output data/temp logs
	@echo "$(GREEN)Configuration initialized!$(NC)"

##@ Git Workflow

git-status: ## Show git status and branch info
	@echo "$(BLUE)Git Status:$(NC)"
	@git status
	@echo ""
	@echo "$(BLUE)Current Branch:$(NC)"
	@git branch --show-current

commit: ## Quick commit with message (use: make commit MSG="your message")
	@if [ -z "$(MSG)" ]; then \
		echo "$(RED)Error: Please provide commit message$(NC)"; \
		echo "Usage: make commit MSG=\"your commit message\""; \
		exit 1; \
	fi
	@git add .
	@git commit -m "$(MSG)"
	@echo "$(GREEN)Changes committed!$(NC)"

# Note: Additional targets can be added as the project evolves
