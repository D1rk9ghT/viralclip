"""
Firebase Authentication middleware for FastAPI.
Verifies Firebase ID tokens and extracts user identity.
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger
from typing import Optional
import httpx

from app.config import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)

# Firebase public keys endpoint for token verification
FIREBASE_VERIFY_URL = (
    "https://identitytoolkit.googleapis.com/v1/accounts:lookup"
)


class FirebaseUser:
    """Represents a verified Firebase user."""

    def __init__(self, uid: str, email: str, name: Optional[str] = None,
                 photo_url: Optional[str] = None):
        self.uid = uid
        self.email = email
        self.name = name
        self.photo_url = photo_url

    def __repr__(self):
        return f"FirebaseUser(uid={self.uid}, email={self.email})"


async def verify_firebase_token(token: str) -> Optional[FirebaseUser]:
    """
    Verify a Firebase ID token by calling Google's token info endpoint.
    This is a lightweight approach that doesn't require firebase-admin SDK
    (which has heavy native dependencies). For production at scale,
    switch to firebase-admin.verify_id_token().
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Use Google's tokeninfo endpoint to verify the token
            resp = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
            )

            if resp.status_code != 200:
                logger.warning(f"Token verification failed: {resp.status_code}")
                return None

            data = resp.json()

            # Verify the audience matches our Firebase project
            aud = data.get("aud", "")
            if settings.FIREBASE_PROJECT_ID not in aud:
                logger.warning(f"Token audience mismatch: {aud}")
                return None

            return FirebaseUser(
                uid=data.get("sub", ""),
                email=data.get("email", ""),
                name=data.get("name"),
                photo_url=data.get("picture"),
            )
    except httpx.TimeoutException:
        logger.error("Firebase token verification timed out")
        return None
    except Exception as e:
        logger.error(f"Firebase token verification error: {e}")
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> FirebaseUser:
    """
    FastAPI dependency that extracts and verifies the Firebase user
    from the Authorization header. Returns 401 if invalid.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await verify_firebase_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[FirebaseUser]:
    """
    Same as get_current_user but returns None instead of 401
    for endpoints that work with or without auth.
    """
    if not credentials:
        return None
    return await verify_firebase_token(credentials.credentials)
