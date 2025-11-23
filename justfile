default: format lint typecheck test

test:
    uv run pytest

lint:
    uv run ruff check --fix

format:
    uv run ruff format

typecheck:
    uv run ty check
