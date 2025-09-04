import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()
ROUTER_TAGS = ["system"]


@router.get("/health-check", tags=ROUTER_TAGS)
def health_check() -> dict[str, str]:
    return {"status": "ok"}
