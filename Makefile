.PHONY: help up down logs migrate seed test lint fmt ci

help:
	@echo "ProcureAI targets:"
	@echo "  make up        - docker compose up --build"
	@echo "  make down      - stop stack"
	@echo "  make migrate   - alembic upgrade head (in api container)"
	@echo "  make seed      - seed demo data"
	@echo "  make test      - backend pytest"
	@echo "  make lint      - ruff + frontend eslint/tsc"

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f api web

migrate:
	docker compose exec api alembic upgrade head

seed:
	docker compose exec api python -m scripts.seed

test:
	docker compose exec api pytest -q

lint:
	docker compose exec api ruff check app tests scripts
	docker compose exec web npm run lint
	docker compose exec web npm run typecheck
