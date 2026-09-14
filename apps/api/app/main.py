from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import ApiError, api_error_handler, http_error_handler, unhandled_error_handler
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="ProcureAI API",
        description=(
            "AI-powered purchasing decision, execution and validation platform. "
            "The LLM never writes to the database. Deterministic rules own quantity, "
            "budget, MOQ, storage, and purchase-order mutations."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_exception_handler(ApiError, api_error_handler)  # type: ignore[arg-type]
    application.add_exception_handler(HTTPException, http_error_handler)  # type: ignore[arg-type]
    application.add_exception_handler(Exception, unhandled_error_handler)  # type: ignore[arg-type]
    application.include_router(api_router, prefix="/api")
    return application


app = create_app()
