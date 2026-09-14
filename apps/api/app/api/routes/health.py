from fastapi import APIRouter

from app.core.config import get_settings
from app.core.deps import DbSession
from app.infrastructure.redis_client import redis_ok

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/ready", summary="Readiness (database + redis)")
async def ready(db: DbSession) -> dict:
    from sqlalchemy import text

    await db.execute(text("SELECT 1"))
    settings = get_settings()
    redis = await redis_ok()
    return {"status": "ready", "database": True, "redis": redis, "demo_mode": settings.demo_mode}
