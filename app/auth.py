"""
JWT auth for Parkeye API.

Supabase Auth issues JWTs; the backend verifies them and extracts user_id and role.
Use get_current_user as a dependency on protected routes (e.g. admin, feedback).
"""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import settings

security = HTTPBearer(auto_error=False)


class User(BaseModel):
    id: UUID
    role: str


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User:
    """Decode Supabase JWT and return user id and role. Raises 401 if invalid or missing."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing sub",
            headers={"WWW-Authenticate": "Bearer"},
        )
    role = "user"
    if "role" in payload:
        role = payload["role"]
    elif "app_metadata" in payload and isinstance(payload["app_metadata"], dict):
        role = payload["app_metadata"].get("role", "user")
    return User(id=UUID(sub), role=role)
