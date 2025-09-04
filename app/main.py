from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI

from app.api.routes.system import router as system_router
from app.api.routes.webhook import router as webhook_router
from app.core import configure_logging
from app.core.config import settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging(settings.log_level)
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title="Bluedot Notifications",
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    application.include_router(system_router)
    application.include_router(webhook_router)
    return application


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=True)
