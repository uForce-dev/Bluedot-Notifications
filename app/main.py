import uvicorn
from fastapi import FastAPI

from app.api.routes import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    application = FastAPI(title="Bluedot Notifications", version="0.1.0", debug=settings.debug)
    application.include_router(api_router)
    return application


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
