# HeyGen Social Clipper - Makefile
# Build, test, lint, and deployment automation

.PHONY: help install install-dev install-all test test-unit test-integration lint format type-check \
        coverage clean clean-pyc clean-test clean-build clean-data run verify docs build deploy \
        pre-commit security audit

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := pip3
PYTEST := pytest
BLACK := black
ISORT := isort
FLAKE8 := flake8
MYPY := mypy
RUFF := ruff
VENV := venv
SRC_DIR := src
TEST_DIR := tests
DOCS_DIR := docs
DATA_DIR := data

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
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt
	$(PIP) install -e .
	@echo "$(GREEN)✓ Production installation complete!$(NC)"
	@echo "$(YELLOW)Run 'make verify' to check environment setup$(NC)"

install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -e ".[dev]"
	@echo "$(GREEN)✓ Development installation complete!$(NC)"
	@echo "$(YELLOW)Run 'make verify' to check environment setup$(NC)"

install-all: ## Install all dependencies (prod + dev + optional)
	@echo "$(BLUE)Installing all dependencies...$(NC)"
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -e ".[all]"
	@echo "$(GREEN)✓ Complete installation finished!$(NC)"

install-webhook: ## Install with webhook server support
	@echo "$(BLUE)Installing with webhook support...$(NC)"
	$(PIP) install -e ".[webhook]"
	@echo "$(GREEN)✓ Webhook dependencies installed!$(NC)"

install-cloud: ## Install with cloud storage support
	@echo "$(BLUE)Installing with cloud storage support...$(NC)"
	$(PIP) install -e ".[cloud]"
	@echo "$(GREEN)✓ Cloud storage dependencies installed!$(NC)"

venv: ## Create virtual environment
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	$(PYTHON) -m venv $(VENV)
	@echo "$(GREEN)✓ Virtual environment created!$(NC)"
	@echo "$(YELLOW)Activate with: source $(VENV)/bin/activate$(NC)"
	@echo "$(YELLOW)Then run: make install-dev$(NC)"

setup: venv install-dev ## Complete development setup (venv + install)
	@echo "$(GREEN)✓ Development environment ready!$(NC)"
	@echo "$(YELLOW)Run 'make verify' to validate setup$(NC)"

##@ Code Quality

lint: ## Run all linters (ruff + flake8)
	@echo "$(BLUE)Running linters...$(NC)"
	$(RUFF) check $(SRC_DIR) $(TEST_DIR)
	$(FLAKE8) $(SRC_DIR) $(TEST_DIR) --max-line-length=100
	@echo "$(GREEN)✓ Linting complete!$(NC)"

lint-fix: ## Auto-fix linting issues where possible
	@echo "$(BLUE)Auto-fixing linting issues...$(NC)"
	$(RUFF) check --fix $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)✓ Auto-fixes applied!$(NC)"

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	$(BLACK) $(SRC_DIR) $(TEST_DIR)
	$(ISORT) $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)✓ Code formatting complete!$(NC)"

format-check: ## Check code formatting without making changes
	@echo "$(BLUE)Checking code formatting...$(NC)"
	$(BLACK) --check $(SRC_DIR) $(TEST_DIR)
	$(ISORT) --check-only $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)✓ Format check complete!$(NC)"

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checker...$(NC)"
	$(MYPY) $(SRC_DIR)
	@echo "$(GREEN)✓ Type checking complete!$(NC)"

check: format-check lint type-check ## Run all code quality checks
	@echo "$(GREEN)✓ All checks passed!$(NC)"

##@ Testing

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	$(PYTEST) $(TEST_DIR) -v
	@echo "$(GREEN)✓ Tests complete!$(NC)"

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	$(PYTEST) $(TEST_DIR)/unit -v -m "unit"
	@echo "$(GREEN)✓ Unit tests complete!$(NC)"

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	$(PYTEST) $(TEST_DIR)/integration -v -m "integration"
	@echo "$(GREEN)✓ Integration tests complete!$(NC)"

test-fast: ## Run tests excluding slow tests
	@echo "$(BLUE)Running fast tests...$(NC)"
	$(PYTEST) $(TEST_DIR) -v -m "not slow"
	@echo "$(GREEN)✓ Fast tests complete!$(NC)"

test-watch: ## Watch for changes and run tests automatically
	@echo "$(BLUE)Watching for changes...$(NC)"
	pytest-watch $(TEST_DIR)

coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(PYTEST) $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term --cov-report=xml
	@echo "$(GREEN)✓ Coverage report generated!$(NC)"
	@echo "$(YELLOW)Open htmlcov/index.html to view detailed report$(NC)"

coverage-report: ## Open coverage report in browser
	@echo "$(BLUE)Opening coverage report...$(NC)"
	@command -v open >/dev/null 2>&1 && open htmlcov/index.html || \
	command -v xdg-open >/dev/null 2>&1 && xdg-open htmlcov/index.html || \
	echo "$(YELLOW)Please open htmlcov/index.html manually$(NC)"

##@ Security & Audit

security: ## Run security checks with bandit
	@echo "$(BLUE)Running security scan...$(NC)"
	bandit -r $(SRC_DIR) -f json -o bandit-report.json || true
	bandit -r $(SRC_DIR) --severity-level medium
	@echo "$(GREEN)✓ Security scan complete!$(NC)"

audit: ## Audit dependencies for known vulnerabilities
	@echo "$(BLUE)Auditing dependencies...$(NC)"
	pip-audit
	@echo "$(GREEN)✓ Dependency audit complete!$(NC)"

##@ Pre-commit

pre-commit-install: ## Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	pre-commit install
	@echo "$(GREEN)✓ Pre-commit hooks installed!$(NC)"

pre-commit: ## Run pre-commit hooks on all files
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	pre-commit run --all-files
	@echo "$(GREEN)✓ Pre-commit checks complete!$(NC)"

##@ Development

run: ## Run CLI tool (example command)
	@echo "$(BLUE)Running heygen-clipper...$(NC)"
	heygen-clipper --help

run-webhook: ## Start webhook server (development)
	@echo "$(BLUE)Starting webhook server...$(NC)"
	heygen-clipper webhook --host localhost --port 8000 --config config/brand.yaml --output-dir data/output

watch: ## Watch directory for new videos (development)
	@echo "$(BLUE)Watching for new videos...$(NC)"
	heygen-clipper watch --watch-dir data/input --config config/brand.yaml --output-dir data/output

verify: ## Verify environment setup
	@echo "$(BLUE)Verifying environment...$(NC)"
	@$(PYTHON) scripts/verify_env.py
	@echo "$(GREEN)✓ Environment verification complete!$(NC)"

##@ Documentation

docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	@cd $(DOCS_DIR) && make html
	@echo "$(GREEN)✓ Documentation generated!$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation at http://localhost:8080...$(NC)"
	@cd $(DOCS_DIR)/_build/html && $(PYTHON) -m http.server 8080

docs-clean: ## Clean documentation build
	@echo "$(BLUE)Cleaning documentation...$(NC)"
	@cd $(DOCS_DIR) && make clean
	@echo "$(GREEN)✓ Documentation cleaned!$(NC)"

##@ Building & Packaging

build: clean ## Build distribution packages
	@echo "$(BLUE)Building distribution packages...$(NC)"
	$(PYTHON) -m build
	@echo "$(GREEN)✓ Build complete! Packages in dist/$(NC)"

build-check: build ## Build and validate package
	@echo "$(BLUE)Validating package...$(NC)"
	twine check dist/*
	@echo "$(GREEN)✓ Package validation complete!$(NC)"

##@ Cleaning

clean: clean-pyc clean-test clean-build ## Remove all build, test, and cache files
	@echo "$(GREEN)✓ Cleanup complete!$(NC)"

clean-pyc: ## Remove Python cache files
	@echo "$(BLUE)Cleaning Python cache files...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type f -name '*~' -delete
	@echo "$(GREEN)✓ Python cache cleaned!$(NC)"

clean-test: ## Remove test and coverage artifacts
	@echo "$(BLUE)Cleaning test artifacts...$(NC)"
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf coverage.xml
	rm -rf .tox/
	rm -f bandit-report.json
	@echo "$(GREEN)✓ Test artifacts cleaned!$(NC)"

clean-build: ## Remove build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf $(SRC_DIR)/*.egg-info
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	@echo "$(GREEN)✓ Build artifacts cleaned!$(NC)"

clean-data: ## Clean temporary and output data (CAREFUL!)
	@echo "$(RED)WARNING: This will delete all temporary and output files!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf $(DATA_DIR)/temp/*; \
		rm -rf $(DATA_DIR)/output/*; \
		echo "$(GREEN)✓ Data cleaned!$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled.$(NC)"; \
	fi

clean-all: clean clean-data ## Remove all build artifacts and data
	@echo "$(GREEN)✓ Complete cleanup finished!$(NC)"

##@ Deployment

deploy-test: build-check ## Deploy to Test PyPI
	@echo "$(BLUE)Deploying to Test PyPI...$(NC)"
	twine upload --repository testpypi dist/*
	@echo "$(GREEN)✓ Deployed to Test PyPI!$(NC)"

deploy-prod: build-check ## Deploy to production PyPI
	@echo "$(RED)Deploying to Production PyPI...$(NC)"
	@read -p "Are you sure you want to deploy to production? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		twine upload dist/*; \
		echo "$(GREEN)✓ Deployed to PyPI!$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled.$(NC)"; \
	fi

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t heygen-clipper:latest .
	@echo "$(GREEN)✓ Docker image built!$(NC)"

docker-run: ## Run Docker container
	@echo "$(BLUE)Running Docker container...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Container running!$(NC)"

docker-stop: ## Stop Docker container
	@echo "$(BLUE)Stopping Docker container...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Container stopped!$(NC)"

##@ Utilities

version: ## Show version information
	@echo "$(BLUE)Version Information:$(NC)"
	@echo "Python: $$($(PYTHON) --version)"
	@echo "pip: $$($(PIP) --version)"
	@echo "FFmpeg: $$(ffmpeg -version 2>/dev/null | head -n1 || echo 'Not installed')"
	@echo "Package: $$($(PYTHON) -c 'import src; print(src.__version__)' 2>/dev/null || echo 'Not installed')"

env-check: ## Check environment setup
	@echo "$(BLUE)Environment Check:$(NC)"
	@command -v python3 >/dev/null 2>&1 && echo "$(GREEN)✓$(NC) Python 3 installed" || echo "$(RED)✗$(NC) Python 3 not found"
	@command -v ffmpeg >/dev/null 2>&1 && echo "$(GREEN)✓$(NC) FFmpeg installed" || echo "$(RED)✗$(NC) FFmpeg not found"
	@command -v git >/dev/null 2>&1 && echo "$(GREEN)✓$(NC) Git installed" || echo "$(RED)✗$(NC) Git not found"
	@[ -f .env ] && echo "$(GREEN)✓$(NC) .env file exists" || echo "$(YELLOW)⚠$(NC) .env file not found (copy from .env.example)"
	@$(PYTHON) scripts/verify_env.py 2>/dev/null || echo "$(YELLOW)⚠$(NC) Run 'make verify' for detailed check"

init-config: ## Initialize configuration files from examples
	@echo "$(BLUE)Initializing configuration...$(NC)"
	@[ ! -f .env ] && cp .env.example .env && echo "$(GREEN)✓ Created .env$(NC)" || echo "$(YELLOW).env already exists$(NC)"
	@mkdir -p config data/output data/temp logs
	@echo "$(GREEN)✓ Configuration initialized!$(NC)"

deps-update: ## Update all dependencies to latest compatible versions
	@echo "$(BLUE)Updating dependencies...$(NC)"
	@echo "$(YELLOW)This will update requirements.txt to latest compatible versions$(NC)"
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		pip-compile --upgrade requirements.in -o requirements.txt; \
		pip-compile --upgrade requirements-dev.in -o requirements-dev.txt; \
		echo "$(GREEN)✓ Dependencies updated!$(NC)"; \
		echo "$(YELLOW)Review changes and test before committing$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled.$(NC)"; \
	fi

deps-outdated: ## Show outdated dependencies
	@echo "$(BLUE)Checking for outdated dependencies...$(NC)"
	$(PIP) list --outdated

freeze: ## Freeze current environment to requirements-lock.txt
	@echo "$(BLUE)Freezing dependencies...$(NC)"
	$(PIP) freeze > requirements-lock.txt
	@echo "$(GREEN)✓ Dependencies frozen to requirements-lock.txt$(NC)"

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
	@echo "$(GREEN)✓ Changes committed!$(NC)"

##@ CI/CD

ci: clean install-dev check test coverage security ## Run full CI pipeline locally
	@echo "$(GREEN)✓ CI pipeline complete!$(NC)"

ci-fast: clean install-dev format-check lint test-fast ## Run fast CI checks
	@echo "$(GREEN)✓ Fast CI checks complete!$(NC)"

# Note: Additional targets can be added as the project evolves
