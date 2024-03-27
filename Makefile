install:
	poetry install --no-interaction

build:
	poetry build

lint:
	poetry install --no-interaction --no-root --with tests
	poetry run ruff check .
	poetry run mypy pylspclient

test:
	poetry install --no-interaction --no-root --with tests
	poetry run pytest $(PYTEST_FLAGS)

publish:
	poetry install --no-interaction --no-root --with publish
	TWINE_USERNAME="__token__" \
	TWINE_PASSWORD="$(PASSWORD)" \
	poetry run twine upload dist/*

bump:
	poetry version patch
