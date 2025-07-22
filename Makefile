.PHONY: install install-all install-dev run run-sse run-web lint format test build publish clean

# Installation targets
install:
	uv sync

install-all:
	uv sync --extra all

install-dev: 
	uv sync --extra dev

install-web:
	uv sync --extra web --extra auth

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

build: clean
	uv run python -m build

publish: build
	uv run python -m twine upload --config-file .pypirc dist/*
