from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ApiError
from app.core.security import decode_token
from app.db import get_db
from app.models.entities import User

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise ApiError(401, "unauthorized", "Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise ApiError(401, "unauthorized", "Invalid token") from exc
    email = payload.get("sub")
    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if not user:
        raise ApiError(401, "unauthorized", "User not found")
    return user


async def require_approver(user: Annotated[User, Depends(get_current_user)]) -> User:
    if get_settings().demo_mode:
        return user
    if user.role not in ("approver", "admin"):
        raise ApiError(403, "forbidden", "Approver role required")
    return user
