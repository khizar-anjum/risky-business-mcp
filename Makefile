.PHONY: help install install-dev test lint format clean build publish run

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package in development mode
	pip install -e .

install-dev: ## Install the package with development dependencies
	pip install -e ".[dev]"

install-test: ## Install the package with test dependencies
	pip install -e ".[test]"

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=. --cov-report=html --cov-report=term-missing

lint: ## Run linting checks
	flake8 .
	mypy .
	black --check .
	isort --check-only .

format: ## Format code
	black .
	isort .

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: ## Build the package
	python -m build

build-wheel: ## Build wheel only
	python -m build --wheel

build-sdist: ## Build source distribution only
	python -m build --sdist

publish: ## Publish to PyPI (requires proper credentials)
	python -m twine upload dist/*

run: ## Run the MCP server
	python main.py

run-dev: ## Run the MCP server in development mode
	uvicorn main:mcp --reload --host 0.0.0.0 --port 8000

check-deps: ## Check for outdated dependencies
	pip list --outdated

update-deps: ## Update dependencies to latest versions
	pip install --upgrade -r requirements.txt

docker-build: ## Build Docker image
	docker build -t risky-business-mcp .

docker-run: ## Run Docker container
	docker run -p 8000:8000 risky-business-mcp

venv: ## Create virtual environment
	python -m venv venv
	@echo "Virtual environment created. Activate it with:"
	@echo "source venv/bin/activate  # On Unix/macOS"
	@echo "venv\\Scripts\\activate     # On Windows"

setup: venv install-dev ## Set up development environment
	@echo "Development environment set up successfully!"
	@echo "Activate the virtual environment and run 'make run' to start the server"
