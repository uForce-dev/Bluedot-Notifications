from fastapi import APIRouter

router = APIRouter()
ROUTER_TAGS = ["system"]


@router.get("/health-check", tags=ROUTER_TAGS)
def health_check() -> dict[str, str]:
    return {"status": "ok"}
