import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
import app.models  # noqa: F401
from app.routers import auth, credits, transcribe, users, webhooks
from app.telemetry import setup_telemetry

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
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
