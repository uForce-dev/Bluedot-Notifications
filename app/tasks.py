import logging
from datetime import datetime, timedelta
from typing import Any

from celery import Celery
from celery.signals import worker_process_init

from app.api.scheme import BluedotMeetingSummaryCreatedEvent
from app.core.config import settings
from app.loader import init_mm_driver
from app.core import configure_logging
from app.db.session import SessionLocal
from app.services.google_calendar import GoogleCalendarService
from app.infrastructure.mattermost import MattermostClient
from app.infrastructure.repositories import SQLAlchemyNotificationLogRepository
from app.application.reminder import ReminderService

logger = logging.getLogger(__name__)

celery_app = Celery("tasks", broker=settings.redis_url, backend=settings.redis_url)


@worker_process_init.connect
def init_mattermost(**kwargs) -> None:
    configure_logging(settings.log_level)
    init_mm_driver()


@celery_app.task(name="process_bluedot_webhook")
def process_bluedot_webhook(event_data: dict) -> None:
    event = BluedotMeetingSummaryCreatedEvent.model_validate(event_data)

    root_posts: dict[str, tuple[str, str]] = {}
    next_data: dict[str, tuple[str | None, datetime | None, datetime | None]] = {}
    for attendee_email in event.attendees:
        # Pre-compute next occurrence (once per attendee) and send summary-ready DM
        meeting_link_resolved: str | None = None
        next_occurrence: datetime | None = None
        try:
            calendar_service = GoogleCalendarService(user_email=attendee_email)
            if calendar_service.is_ready():
                meeting_link_resolved, next_occurrence = (
                    calendar_service.find_recurring_event_next_occurrence(
                        meeting_link=event.meeting_link,
                        start_time=event.created_at,
                    )
                )
        except Exception:
            logger.exception("Failed to compute next occurrence for summary message")

        reminder_time: datetime | None = None
        if next_occurrence:
            reminder_time = datetime.now() + timedelta(hours=1)

        next_data[attendee_email] = (
            meeting_link_resolved or event.meeting_link,
            next_occurrence,
            reminder_time,
        )

        with SessionLocal() as db:
            try:
                service = ReminderService(
                    mm=MattermostClient(),
                    logs=SQLAlchemyNotificationLogRepository(db),
                )
                res = service.send_summary_ready(
                    user_email=attendee_email,
                    title=event.title,
                    meeting_link=event.meeting_link,
                    summary=event.summary_v2,
                    reminder_time=reminder_time,
                )
                if res:
                    root_posts[attendee_email] = res
            except Exception:
                logger.exception("Failed to send immediate summary notification")

    for attendee_email in event.attendees:
        try:
            meeting_link, next_occurrence, reminder_time = next_data.get(
                attendee_email, (event.meeting_link, None, None)
            )
            if next_occurrence is None:
                calendar_service = GoogleCalendarService(user_email=attendee_email)
                if calendar_service.is_ready():
                    meeting_link, next_occurrence = (
                        calendar_service.find_recurring_event_next_occurrence(
                            meeting_link=event.meeting_link,
                            start_time=event.created_at,
                        )
                    )
            if reminder_time is None and next_occurrence is not None:
                reminder_time = datetime.now() + timedelta(hours=1)

            logger.info(
                f"For user {attendee_email}, next_occurrence: {next_occurrence}"
            )

            if next_occurrence and reminder_time:
                # reminder_time could be computed as next_occurrence - timedelta(hours=1)
                send_mattermost_reminder.apply_async(
                    args=[
                        meeting_link,
                        event.model_dump(by_alias=True, mode="json"),
                        next_occurrence.isoformat() if next_occurrence else None,
                        root_posts,
                    ],
                    eta=reminder_time,
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
    meeting_link: str,
    event_data: dict[str, Any],
    meeting_time_iso: str | None,
    root_posts: dict[str, tuple[str, str]],
) -> None:
    event = BluedotMeetingSummaryCreatedEvent.model_validate(event_data)

    for email in event.attendees:
        db = SessionLocal()
        try:
            meeting_time = (
                datetime.fromisoformat(meeting_time_iso) if meeting_time_iso else None
            )
            service = ReminderService(
                mm=MattermostClient(),
                logs=SQLAlchemyNotificationLogRepository(db),
            )
            root_info = root_posts.get(email)
            if root_info:
                root_post_id, channel_id = root_info
                service.reply_reminder_in_thread(
                    root_post_id=root_post_id,
                    channel_id=channel_id,
                    user_email=email,
                    title=event.title,
                    meeting_link=meeting_link,
                    meeting_time=meeting_time,
                )
            else:
                service.send_reminder(
                    user_email=email,
                    title=event.title,
                    meeting_link=meeting_link,
                    meeting_time=meeting_time,
                )

        except Exception as e:
            logger.exception(
                f"It was not possible to send a reminder to the user {email}: {e}",
                exc_info=True,
            )
        finally:
            db.close()
