.PHONY: setup check test lint contracts workflow

setup:
	uv sync --frozen --group dev

check:
	uv run python scripts/validate_repository.py

test:
	uv run pytest -q

lint:
	uv run ruff check .

contracts:
	uv run pytest -q tests/test_repository_contracts.py

workflow:
	./go validate .
