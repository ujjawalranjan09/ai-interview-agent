.PHONY: install dev up down test lint migrate makemigration

install:
	cd apps/api && python -m venv .venv && .venv\Scripts\activate && pip install -e ".[dev]"
	cd apps/web && pnpm install

dev:
	docker compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml up

up:
	docker compose -f infra/docker-compose.yml up -d

down:
	docker compose -f infra/docker-compose.yml down

test:
	cd apps/api && pytest -v
	cd apps/web && pnpm test

lint:
	cd apps/api && ruff check .
	cd apps/web && pnpm lint

migrate:
	cd apps/api && alembic upgrade head

makemigration:
	cd apps/api && alembic revision --autogenerate -m "$(msg)"
