# Makefile for Georgia Currency Exchange Bot

# Define the command to run Python
# This can be overridden with environment variables
CMD:=uv run

.PHONY: lint format test test_with_coverage

lint:
	${CMD} ruff check --fix;
	${CMD} mypy --namespace-packages -p src;

format:
	${CMD} ruff format;

test_with_coverage:
	$(CMD) coverage run -m pytest ;\
    $(CMD) coverage report ;\
    $(CMD) coverage xml

test:
	${CMD} pytest -v


#################################
start_sync:
	${CMD} python -m src.start_sync

start_bot:
	${CMD} python -m src.start_bot
