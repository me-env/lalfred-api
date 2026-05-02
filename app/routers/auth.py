from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import GoogleAuthURL
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")


@router.get("/google/login", response_model=GoogleAuthURL)
async def google_login():
    return GoogleAuthURL(url=auth_service.get_login_url())


@router.get("/google/callback")
async def google_callback(request: Request, code: str, db: AsyncSession = Depends(get_db)):
    _user, deeplink = await auth_service.handle_callback(db, code)
    await db.commit()
    return templates.TemplateResponse(request, "auth_success.html", {"deeplink": deeplink})
