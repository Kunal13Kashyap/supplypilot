from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.core.deps import DbSession, get_current_user
from app.core.errors import ApiError
from app.core.security import create_access_token, verify_password
from app.models.entities import User
from app.schemas.api import LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse, summary="Demo login")
async def login(body: LoginRequest, db: DbSession) -> TokenResponse:
    user = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise ApiError(401, "invalid_credentials", "Email or password is incorrect")
    token = create_access_token(user.email, user.role, extra={"name": user.full_name})
    return TokenResponse(access_token=token, role=user.role, email=user.email, full_name=user.full_name)


@router.get("/me", response_model=UserOut)
async def me(user: Annotated[User, Depends(get_current_user)]) -> UserOut:
    return UserOut(email=user.email, full_name=user.full_name, role=user.role)
