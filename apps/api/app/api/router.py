from fastapi import APIRouter

from app.api.routes import auth, cases, dashboard, health, ops

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(cases.router)
api_router.include_router(dashboard.router)
api_router.include_router(ops.router)
