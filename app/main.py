from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging

from app.api.routes.system import router as system_router
from app.api.routes.webhook import router as webhook_router
from app.core import configure_logging, request_id_var
from app.core.config import settings
from app.db import Base, engine
from app.loader import init_mm_driver


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging(settings.log_level)
    init_mm_driver()
    import app.models  # noqa: F401

    if settings.debug:
        Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()


def create_app() -> FastAPI:
    application = FastAPI(
        title="Bluedot Notifications",
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    @application.middleware("http")
    async def add_request_id(request, call_next):
        token = request_id_var.set(
            request.headers.get("X-Request-Id")
            or request.state.__dict__.get("request_id")
            or "-"
        )
        try:
            response = await call_next(request)
            return response
        finally:
            request_id_var.reset(token)

    logger = logging.getLogger("validation")

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        try:
            body_bytes = await request.body()
            body_preview = (
                body_bytes[:2048].decode("utf-8", "ignore") if body_bytes else ""
            )
        except Exception:
            body_preview = ""

        logger.warning(
            "request_validation_failed",
            extra={
                "path": str(request.url.path),
                "method": request.method,
                "query": dict(request.query_params),
                "headers": {k: v for k, v in request.headers.items()},
                "body_preview": body_preview,
                "errors": exc.errors(),
            },
        )
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    application.include_router(system_router)
    application.include_router(webhook_router)
    return application


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.internal_port, reload=True)
