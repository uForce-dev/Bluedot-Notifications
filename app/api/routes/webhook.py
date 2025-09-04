import logging
from http import HTTPStatus

from fastapi import APIRouter, Response

from app.api.scheme import BluedotMeetingSummaryCreatedEvent
from app.tasks import process_bluedot_webhook

logger = logging.getLogger(__name__)

router = APIRouter()
ROUTER_TAGS = ["webhook"]


@router.post("/webhook/bluedot/events", tags=ROUTER_TAGS)
async def webhook(event: BluedotMeetingSummaryCreatedEvent) -> Response:
    logger.info(f"Webhook request received. Queuing task for event: {event.type}")
    process_bluedot_webhook.delay(event.model_dump(by_alias=True, mode="json"))
    return Response(status_code=HTTPStatus.OK)
