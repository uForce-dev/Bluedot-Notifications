import logging
from datetime import datetime, timedelta
from typing import Any

from celery import Celery
from celery.signals import worker_process_init

from app.api.scheme import BluedotMeetingSummaryCreatedEvent
from app.core.config import settings
from app.loader import init_mm_driver, mm_driver
from app.services.google_calendar import GoogleCalendarService

logger = logging.getLogger(__name__)

celery_app = Celery("tasks", broker=settings.redis_url, backend=settings.redis_url)


@worker_process_init.connect
def init_mattermost(**kwargs) -> None:
    init_mm_driver()


@celery_app.task(name="process_bluedot_webhook")
def process_bluedot_webhook(event_data: dict) -> None:
    event = BluedotMeetingSummaryCreatedEvent.model_validate(event_data)

    for attendee_email in event.attendees:
        try:
            calendar_service = GoogleCalendarService(user_email=attendee_email)
            if not calendar_service.is_ready():
                continue

            meeting_name, meeting_link, next_occurrence = (
                calendar_service.find_recurring_event_next_occurrence(
                    meeting_link=event.meeting_link,
                    start_time=event.created_at,
                )
            )

            logger.info(
                f"For user {attendee_email}, next_occurrence: {next_occurrence}"
            )

            if next_occurrence:
                # reminder_time = next_occurrence - timedelta(hours=1)
                reminder_time = datetime.now() + timedelta(minutes=1)
                # send_mattermost_reminder.apply_async(
                #     args=[event.model_dump(by_alias=True, mode="json")],
                #     eta=reminder_time,
                # )
                send_mattermost_reminder.apply_async(
                    args=[
                        meeting_name,
                        meeting_link,
                        event.model_dump(by_alias=True, mode="json"),
                    ],
                )
                logger.info(
                    f"Scheduled reminder for {event.meeting_id} at {reminder_time} "
                    f"for attendees: {event.attendees}"
                )
                break
        except Exception as e:
            logger.error(
                f"Could not process calendar for {attendee_email}. Error: {e}",
                exc_info=True,
            )


@celery_app.task(name="send_mattermost_reminder")
def send_mattermost_reminder(
    meeting_name: str, meeting_link: str, event_data: dict[str, Any]
) -> None:
    event = BluedotMeetingSummaryCreatedEvent.model_validate(event_data)

    me = mm_driver.users.get_user("me")
    bot_user_id = me["id"]

    for email in event.attendees:
        try:
            user = mm_driver.users.get_user_by_email(email)
            print(f"user: {user}")
            user_id = user["id"]
            print(f"user_id: {user_id}")

            dm_channel = mm_driver.channels.create_direct_message_channel(
                [bot_user_id, user_id]
            )

            message = (
                f"📅 **Напоминание о предстоящей встрече: [{meeting_name}]({meeting_link})**\n\n"
                "Вот краткое содержание прошлого созвона:\n\n"
                "---\n\n"
                f"{event.summary_v2}"
            )

            mm_driver.posts.create_post(
                options={"channel_id": dm_channel["id"], "message": message}
            )
            logger.info(f"Sent a DM reminder to the user {email} ({user_id}).")

        except Exception as e:
            logger.exception(
                f"It was not possible to send a reminder to the user {email}: {e}",
                exc_info=True,
            )
