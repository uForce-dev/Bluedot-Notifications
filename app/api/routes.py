import json
import logging
from datetime import datetime
from http import HTTPStatus

from fastapi import APIRouter, Request, Response

logger = logging.getLogger(__name__)

api_router = APIRouter()


@api_router.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok"}


@api_router.post("/webhook", tags=["webhook"])
async def webhook(request: Request) -> Response:
    received_at = datetime.utcnow().isoformat() + "Z"
    body_bytes = await request.body()
    try:
        body_json = json.loads(body_bytes.decode("utf-8")) if body_bytes else None
    except Exception:
        body_json = None

    logger.info(
        "webhook_request",
        extra={
            "path": str(request.url.path),
            "query": dict(request.query_params),
            "headers": {k: v for k, v in request.headers.items()},
            "received_at": received_at,
            "body_bytes_len": len(body_bytes),
            "body_json": body_json,
            "client": request.client.host if request.client else None,
            "method": request.method,
        },
    )

    return Response(status_code=HTTPStatus.OK)


@api_router.get("/webhook", tags=["system"])
def webhook_test():
    return HTTPStatus.OK
