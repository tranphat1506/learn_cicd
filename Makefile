PY ?= python3
VENV := .venv
BIN := $(VENV)/bin

.PHONY: setup seed test lint eval baseline run build up down clean

setup: $(VENV)/bin/activate

$(VENV)/bin/activate: requirements-dev.txt
	$(PY) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements-dev.txt
	@touch $(VENV)/bin/activate

seed:
	$(BIN)/python -m model.seed_artifact

test:
	$(BIN)/pytest --cov=app --cov-report=term-missing --cov-fail-under=80

lint:
	$(BIN)/ruff check .

eval:
	$(BIN)/python -m model.evaluate

baseline:
	$(BIN)/python -m model.evaluate --update-baseline

run:
	$(BIN)/uvicorn app.main:app --reload --port 8000

build:
	docker build -t model-api:local .

up:
	docker compose --profile app up --build -d

down:
	docker compose --profile app down

clean:
	rm -rf $(VENV) .pytest_cache .ruff_cache .coverage htmlcov model/reports
