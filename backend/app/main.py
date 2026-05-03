from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import approvals, chat, codebase, documents, health, llmops, memory, settings, tools
from app.core.config import get_settings
from app.db.database import init_db
from app.services.prompts import seed_prompts
from app.services.tools import register_tools


def create_app() -> FastAPI:
    config = get_settings()
    app = FastAPI(title=config.app_name, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def startup() -> None:
        init_db()
        register_tools()
        seed_prompts()

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "validation_error", "message": "Invalid request payload.", "details": exc.errors()}},
        )

    @app.exception_handler(KeyError)
    async def not_found_handler(request: Request, exc: KeyError):
        return JSONResponse(status_code=404, content={"error": {"code": "not_found", "message": str(exc)}})

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content={"error": {"code": "internal_error", "message": str(exc)}})

    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(documents.router)
    app.include_router(memory.router)
    app.include_router(tools.router)
    app.include_router(approvals.router)
    app.include_router(codebase.router)
    app.include_router(llmops.router)
    app.include_router(settings.router)
    return app


app = create_app()

