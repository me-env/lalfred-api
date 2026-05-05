# Lalfred API

FastAPI backend for the Lalfred dictation application.

## Features

- **Google OAuth** — Sign in with Google, JWT-based sessions
- **Credits system** — Purchase credits via Lemon Squeezy, consumed on transcription
- **Transcription proxy** — Transparent proxy to ElevenLabs Scribe v2
- **OpenTelemetry** — Distributed tracing for all requests, DB queries, and HTTP calls

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
| GET | `/credits/balance` | Credit balance |
| GET | `/credits/transactions` | Transaction history |
| POST | `/transcribe` | Proxy to ElevenLabs Scribe v2 |
| POST | `/webhooks/lemonsqueezy/order-created` | Lemon Squeezy order created webhook |
| POST | `/webhooks/lemonsqueezy/subscription-payment-success` | Lemon Squeezy subscription payment success webhook |

## Environment Variables

See `.env.example` for all required configuration.
