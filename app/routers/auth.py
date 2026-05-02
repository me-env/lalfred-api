import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token
from app.config import settings
from app.database import get_db
from app.models import User
from app.schemas import GoogleAuthURL, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


@router.get("/google/login", response_model=GoogleAuthURL)
async def google_login():
    """Return the Google OAuth2 authorization URL for the client to redirect to."""
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return GoogleAuthURL(url=f"{GOOGLE_AUTH_URL}?{query}")


@router.get("/google/callback", response_model=TokenResponse)
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Exchange Google auth code for tokens, create/update user, return JWT."""
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code with Google",
            )
        tokens = token_resp.json()

        userinfo_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch Google user info",
            )
        userinfo = userinfo_resp.json()

    google_sub = userinfo["sub"]
    email = userinfo["email"]
    name = userinfo.get("name")
    picture = userinfo.get("picture")

    result = await db.execute(select(User).where(User.google_sub == google_sub))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            email=email,
            name=name,
            picture=picture,
            google_sub=google_sub,
            credits=settings.initial_free_credits,
        )
        db.add(user)
    else:
        user.email = email
        user.name = name
        user.picture = picture

    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(user.id)
    return TokenResponse(access_token=access_token)
