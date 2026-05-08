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
COPY start.sh /code/start.sh

ENV PATH="/code/.venv/bin:$PATH"

RUN adduser --disabled-password --no-create-home appuser
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

CMD ["sh", "start.sh"]
