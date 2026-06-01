import urllib.parse
import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.db.models import User
from app.core.auth import get_current_user

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/auth", tags=["oauth"])

from jose import JWTError, jwt
from app.core.security import SECRET_KEY, ALGORITHM
from sqlalchemy import select
from fastapi.responses import RedirectResponse

async def authenticate_from_token(token: str, db: AsyncSession) -> User | None:
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            return None
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalars().first()
    except Exception as e:
        logger.error("jwt decode failed", error=str(e))
        return None

@router.get("/youtube/login")
async def youtube_login(token: str = None):
    settings = get_settings()
    params = {
        "client_id": settings.youtube_client_id,
        "redirect_uri": settings.oauth_redirect_uri + "/youtube/callback",
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/youtube.readonly",
        "access_type": "offline",
        "prompt": "consent",
    }
    if token:
        params["state"] = token
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url)


@router.get("/youtube/callback")
async def youtube_callback(
    code: str,
    state: str = None,
    db: AsyncSession = Depends(get_db)
):
    current_user = await authenticate_from_token(state, db)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated (invalid state token)")

    settings = get_settings()
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": settings.youtube_client_id,
        "client_secret": settings.youtube_client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.oauth_redirect_uri + "/youtube/callback",
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(token_url, data=data)
        if resp.status_code != 200:
            logger.error("youtube oauth failed", response=resp.text)
            raise HTTPException(status_code=400, detail="YouTube OAuth Failed")
        
        tokens = resp.json()
        current_user.youtube_access_token = tokens.get("access_token")
        if "refresh_token" in tokens:
            current_user.youtube_refresh_token = tokens.get("refresh_token")
            
        db.add(current_user)
        await db.commit()
        
    frontend_url = "https://vidcompare-frontend.onrender.com/integrations"
    return RedirectResponse(frontend_url)


@router.get("/instagram/login")
async def instagram_login(token: str = None):
    settings = get_settings()
    params = {
        "client_id": settings.instagram_client_id,
        "redirect_uri": settings.oauth_redirect_uri + "/instagram/callback",
        "response_type": "code",
        "scope": "user_profile,user_media",
    }
    if token:
        params["state"] = token
    url = f"https://api.instagram.com/oauth/authorize?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url)


@router.get("/instagram/callback")
async def instagram_callback(
    code: str,
    state: str = None,
    db: AsyncSession = Depends(get_db)
):
    current_user = await authenticate_from_token(state, db)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated (invalid state token)")

    settings = get_settings()
    token_url = "https://api.instagram.com/oauth/access_token"
    data = {
        "client_id": settings.instagram_client_id,
        "client_secret": settings.instagram_client_secret,
        "grant_type": "authorization_code",
        "redirect_uri": settings.oauth_redirect_uri + "/instagram/callback",
        "code": code,
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(token_url, data=data)
        if resp.status_code != 200:
            logger.error("instagram oauth failed", response=resp.text)
            raise HTTPException(status_code=400, detail="Instagram OAuth Failed")
            
        tokens = resp.json()
        current_user.instagram_access_token = tokens.get("access_token")
        current_user.instagram_user_id = str(tokens.get("user_id"))
        
        db.add(current_user)
        await db.commit()
        
    frontend_url = "https://vidcompare-frontend.onrender.com/integrations"
    return RedirectResponse(frontend_url)
