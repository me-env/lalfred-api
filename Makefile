.PHONY: migrate migration db-reset db-wipe db-current db-history downgrade dev test sort

# Run all pending migrations
db-upgrade:
	uv run alembic upgrade head

# Create a new named migration (usage: make migration name="add users table")
db-revision:
	uv run alembic revision --autogenerate -m "$(name)"

# Downgrade by one revision
downgrade:
	uv run alembic downgrade -1

# Show current migration revision
db-current:
	uv run alembic current

# Show migration history
db-history:
	uv run alembic history --verbose

# Drop all tables and re-run all migrations from scratch
db-reset:
	uv run alembic downgrade base
	uv run alembic upgrade head

# Drop and recreate the public schema (hard reset of all DB objects/data)
db-wipe:
	docker compose exec -T db psql -U lalfred -d lalfred -c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;"

# Start local dev server with reload
dev:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run test suite
test:
	@set -a; . ./.env.test; set +a; uv run pytest

sort:
	uv run isort .

lint:
	uv run mypy .
