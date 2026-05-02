from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models as _models  # noqa: F401
from app.database import engine
from app.routers import auth, credits, transcribe, users, webhooks
from app.telemetry import setup_telemetry


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(title="L'Alfred API", version="0.1.0", lifespan=lifespan)

setup_telemetry(app)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(credits.router)
app.include_router(transcribe.router)
app.include_router(webhooks.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
