all: format lint

format:
	poetry run black .
	poetry run isort .

lint:
	poetry run pflake8 .

check: format lint