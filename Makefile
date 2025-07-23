.PHONY: install install-all install-dev install-prod setup-dev init-dev init-prod check-env run run-sse run-web lint format test build publish clean validate help

# Environment detection
DEV_ENV_FILE := .env.development
PROD_ENV_FILE := .env
IS_DEV := $(shell test -f $(DEV_ENV_FILE) && echo "true" || echo "false")

# Installation targets
install:
	@if [ "$(IS_DEV)" = "true" ]; then \
		echo "🔧 Development environment detected - setting up virtual environment..."; \
		$(MAKE) setup-dev; \
	else \
		echo "🚀 Production environment detected - installing dependencies..."; \
		$(MAKE) install-prod; \
	fi

install-all:
	uv sync --extra all

install-dev: 
	uv sync --extra dev

install-prod:
	uv sync --no-dev --extra web --extra auth --extra monitoring

install-web:
	uv sync --extra web --extra auth

# Development setup (creates venv and installs dev dependencies)
setup-dev:
	@echo "🔧 Setting up development environment..."
	@if command -v uv >/dev/null 2>&1; then \
		echo "✅ uv found"; \
	else \
		echo "❌ uv not found. Please install uv first: curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		exit 1; \
	fi
	@echo "📦 Creating virtual environment and installing dependencies..."
	uv sync --extra dev --extra web --extra auth
	@echo "✅ Development environment ready!"
	@echo "💡 You can now run: make run-web"

# Development targets  
run:
	uv run python src

run-sse:
	uv run python src --transport sse

run-web:
	uv run python src --transport http --host 0.0.0.0 --port 8000

run-web-auth:
	uv run python src --transport http --host 0.0.0.0 --port 8000 --require-auth

test:
	uv run python src --test

# Code quality
lint:
	uv run ruff check src --fix

format:
	uv run ruff format src

# Testing
pytest:
	uv run pytest

# Build and publish
clean:
	rm -rf dist/ build/ *.egg-info/

# Validation
validate:
	uv run python validate_setup.py

# Environment management
check-env:
	@echo "🔍 Environment Check:"
	@echo "  - Development file (.env.development): $(shell test -f .env.development && echo "✅ Found" || echo "❌ Not found")"
	@echo "  - Production file (.env): $(shell test -f .env && echo "✅ Found" || echo "❌ Not found")"
	@echo "  - Current mode: $(shell test -f .env.development && echo "Development" || echo "Production")"
	@echo "  - uv version: $(shell uv --version 2>/dev/null || echo "Not installed")"
	@echo "  - Python version: $(shell uv run python --version 2>/dev/null || echo "Not available")"

init-dev:
	@echo "🚀 Initializing development environment..."
	@if [ ! -f .env.development ]; then \
		echo "📝 Creating .env.development file..."; \
		cp .env.example .env.development || touch .env.development; \
	fi
	$(MAKE) setup-dev
	@echo "✅ Development environment initialized!"
	@echo "💡 Edit .env.development with your settings, then run: make run-web"

init-prod:
	@echo "🚀 Initializing production environment..."
	@if [ ! -f .env ]; then \
		echo "📝 Creating .env file..."; \
		cp .env.example .env || touch .env; \
	fi
	$(MAKE) install-prod
	@echo "✅ Production environment initialized!"
	@echo "⚠️  Don't forget to configure your .env file with production settings!"

# Help target
help:
	@echo "🔗 OpenMetadata MCP Server - Available Commands"
	@echo "================================================"
	@echo ""
	@echo "🏗️  Environment Setup:"
	@echo "  make init-dev          Initialize development environment"
	@echo "  make init-prod         Initialize production environment"
	@echo "  make install           Auto-detect and install (dev/prod)"
	@echo "  make check-env         Check current environment status"
	@echo ""
	@echo "📦 Installation:"
	@echo "  make install-all       Install all dependencies"
	@echo "  make install-dev       Install development dependencies"
	@echo "  make install-prod      Install production dependencies only"
	@echo "  make install-web       Install web server dependencies"
	@echo ""
	@echo "🚀 Running:"
	@echo "  make run               Run MCP server (stdio mode)"
	@echo "  make run-sse           Run with SSE transport"
	@echo "  make run-web           Run web server (no auth)"
	@echo "  make run-web-auth      Run web server with authentication"
	@echo "  make test              Run test mode"
	@echo ""
	@echo "🧹 Code Quality:"
	@echo "  make lint              Run linter and fix issues"
	@echo "  make format            Format code"
	@echo "  make pytest            Run pytest"
	@echo "  make validate          Validate setup"
	@echo ""
	@echo "📦 Build & Deploy:"
	@echo "  make clean             Clean build artifacts"
	@echo "  make build             Build distribution packages"
	@echo "  make publish           Publish to PyPI"
	@echo ""
	@echo "❓ Help:"
	@echo "  make help              Show this help message"

build: clean
	uv run python -m build

publish: build
	uv run python -m twine upload --config-file .pypirc dist/*
