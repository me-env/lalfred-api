import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models as _models  # noqa: F401
from app.database import engine
from app.logging_config import configure_logging
from app.routers import auth, releases, users
from app.telemetry import setup_telemetry

configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(title="L'Alfred API", version="0.1.0", lifespan=lifespan)

setup_telemetry(app)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(releases.router)


@app.get("/health")
async def health():
    logging.info("Health check")
    return {"status": "ok"}
