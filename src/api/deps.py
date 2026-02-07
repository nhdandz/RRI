"""FastAPI dependencies for dependency injection."""

from typing import Annotated, Generic, TypeVar

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.security import decode_token
from src.storage.database import get_session

T = TypeVar("T")

bearer_scheme = HTTPBearer(auto_error=False)


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    skip: int
    limit: int


async def get_db() -> AsyncSession:
    async for session in get_session():
        yield session


def get_config() -> Settings:
    return get_settings()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: AsyncSession = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    from src.storage.models.user import User

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: AsyncSession = Depends(get_db),
):
    """Returns the current user if a valid token is provided, otherwise None."""
    if credentials is None:
        return None
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        return None

    from src.storage.models.user import User

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        return None
    return user


SettingsDep = Annotated[Settings, Depends(get_config)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
get_current_user_dep = Annotated[object, Depends(get_current_user)]
get_optional_user_dep = Annotated[object | None, Depends(get_optional_user)]
