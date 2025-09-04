import logging
from http import HTTPStatus

from fastapi import APIRouter, Response

from app.api.scheme import BluedotMeetingSummaryCreatedEvent

logger = logging.getLogger(__name__)

router = APIRouter()
ROUTER_TAGS = ["webhook"]


@router.post("/webhook/bluedot/events", tags=ROUTER_TAGS)
async def webhook(event: BluedotMeetingSummaryCreatedEvent) -> Response:
    logger.info(f"Webhook request received. Queuing task for event: {event.type}")
    return Response(status_code=HTTPStatus.OK)
