.PHONY: up down logs db-upgrade db-revision db-reset db-wipe db-current db-history downgrade dev test sort lint

COMPOSE := docker compose -f docker-compose.dev.yml
EXEC_API := $(COMPOSE) exec -T api

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs api -f --tail=300

build:
	$(COMPOSE) build

# Run all pending migrations (inside the api container so env + DB are wired)
db-upgrade:
	$(EXEC_API) alembic upgrade head

# Create a new named migration (usage: make db-revision name="add users table")
db-revision:
	$(EXEC_API) alembic revision --autogenerate -m "$(name)"

# Downgrade by one revision
downgrade:
	$(EXEC_API) alembic downgrade -1

# Show current migration revision
db-current:
	$(EXEC_API) alembic current

# Show migration history
db-history:
	$(EXEC_API) alembic history --verbose

# Drop all tables and re-run all migrations from scratch
db-reset:
	$(EXEC_API) alembic downgrade base
	$(EXEC_API) alembic upgrade head

# Drop and recreate the public schema (hard reset of all DB objects/data)
db-wipe:
	$(COMPOSE) exec -T db psql -U lalfred -d lalfred -c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;"

# Start the dev stack in the foreground (api + db with hot reload)
dev:
	$(COMPOSE) up

# Run test suite (locally; uses sqlite in-memory, no DB needed)
test:
	@set -a; . ./.env.test; set +a; uv run pytest

sort:
	uv run isort .

lint:
	uv run mypy . --exclude tests
