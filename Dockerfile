FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /code

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

RUN python -m compileall -b -q app/
RUN find app/ -name "*.py" -delete

FROM python:3.12-slim

WORKDIR /code

COPY --from=builder /code/.venv /code/.venv
COPY --from=builder /code/app /code/app
COPY --from=builder /code/alembic /code/alembic
COPY --from=builder /code/alembic.ini /code/alembic.ini

ENV PATH="/code/.venv/bin:$PATH"

RUN adduser --disabled-password --no-create-home appuser
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
