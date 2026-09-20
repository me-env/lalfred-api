# L'Alfred API

FastAPI backend for [L'Alfred](https://github.com/me-env/lalfred-ios), a macOS
dictation app.

It handles accounts and update delivery — nothing else. The app talks to the
STT provider directly with the user's own key, so there is no transcription
proxy, no billing and no credits here.

## Features

- **Google OAuth** — sign in with Google, JWT-based sessions
- **Releases** — Sparkle appcast feed and download redirects for the macOS app

## Quick start

```sh
cp .env.example .env    # fill in your own values
make dev                # docker compose up
```

The API is available at `http://localhost:8000`, OpenAPI docs at `/docs`.

Common tasks:

```sh
make up            # start in the background
make down          # stop
make logs          # tail logs
make db-upgrade    # run migrations
make test          # pytest (sqlite in-memory, no DB needed)
make lint          # mypy
```

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/) for anything run
outside Docker.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/auth/google/login` | Get Google OAuth URL |
| GET | `/auth/google/callback` | Google OAuth callback |
| GET | `/users/me` | Current user profile |
| GET | `/releases/appcast.xml` | Sparkle appcast feed (302 to the bucket) |
| GET | `/releases/download/latest` | Always-latest DMG download (302) |
| GET | `/releases/files/{file}` | Stable per-artefact download URLs (302) |

## Configuration

See `.env.example` for every required variable.

## License

MIT
