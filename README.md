# Lalfred API

FastAPI backend for the Lalfred dictation application.

## Features

- **Google OAuth** — Sign in with Google, JWT-based sessions
- **Releases** — Sparkle appcast feed and download redirects for the macOS app
- **OpenTelemetry** — Distributed tracing for all requests, DB queries, and HTTP calls

The app talks to the STT/LLM providers directly with the user's own keys —
there is no transcription proxy, no billing and no credits here.

## Quick Start

```bash
cp .env.example .env
# Fill in your secrets in .env

docker compose up --build
```

The API is available at `http://localhost:8000`. OpenAPI docs at `/docs`.

## Development (without Docker)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start Postgres (e.g. via docker)
docker compose up db -d

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

## Tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/auth/google/login` | Get Google OAuth URL |
| GET | `/auth/google/callback` | Google OAuth callback |
| GET | `/users/me` | Current user profile |
| GET | `/releases/appcast.xml` | Sparkle appcast feed (302 to the bucket) |
| GET | `/releases/download/latest` | Always-latest DMG download (302) |
| GET | `/releases/files/{file}` | Stable per-artefact download URLs (302) |

## Environment Variables

See `.env.example` for all required configuration.
