COMPOSE_FILE := docker-compose.dev.yml
API_URL := http://localhost:8000

YEAR ?= 2024
GP ?= Bahrain
SESSION ?= R
SESSION_ID ?= 1

.PHONY: up down logs restart test lint format ingest stats pace sessions drivers laps shell ps sdk-install sdk-build

up:
	docker compose -f $(COMPOSE_FILE) up --build -d

down:
	docker compose -f $(COMPOSE_FILE) down

logs:
	docker compose -f $(COMPOSE_FILE) logs -f api

restart:
	docker compose -f $(COMPOSE_FILE) restart api

ps:
	docker compose -f $(COMPOSE_FILE) ps

shell:
	docker compose -f $(COMPOSE_FILE) exec api sh

test:
	docker compose -f $(COMPOSE_FILE) exec api pytest tests/ -v

lint:
	docker compose -f $(COMPOSE_FILE) exec api ruff check . && \
		docker compose -f $(COMPOSE_FILE) exec api black --check . && \
		docker compose -f $(COMPOSE_FILE) exec api isort --check-only .

format:
	docker compose -f $(COMPOSE_FILE) exec api black . && \
		docker compose -f $(COMPOSE_FILE) exec api isort .

ingest:
	curl -sS -X POST "$(API_URL)/api/v1/ingest/" \
		-H "Content-Type: application/json" \
		-d '{"year": $(YEAR), "grand_prix": "$(GP)", "session_type": "$(SESSION)"}' | python3 -m json.tool

sessions:
	curl -sS "$(API_URL)/api/v1/sessions/" | python3 -m json.tool

drivers:
	curl -sS "$(API_URL)/api/v1/drivers/" | python3 -m json.tool

laps:
	curl -sS "$(API_URL)/api/v1/sessions/$(SESSION_ID)/laps" | python3 -m json.tool

stats:
	curl -sS "$(API_URL)/api/v1/sessions/$(SESSION_ID)/stats" | python3 -m json.tool

pace:
	curl -sS "$(API_URL)/api/v1/sessions/$(SESSION_ID)/pace?window_size=3&normalize_to_best=true" | python3 -m json.tool

sdk-install:
	pip install -e sdk/f1telemetry_sdk

sdk-build:
	pip install -U build && python3 -m build sdk/f1telemetry_sdk
