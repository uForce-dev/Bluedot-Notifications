import logging
from datetime import timedelta

from celery import Celery
from mattermostdriver import Driver  # noqa

from app.api.scheme import BluedotMeetingSummaryCreatedEvent
from app.core.config import settings
from app.services.google_calendar import GoogleCalendarService

logger = logging.getLogger(__name__)

celery_app = Celery("tasks", broker=settings.redis_url, backend=settings.redis_url)


@celery_app.task(name="process_bluedot_webhook")
def process_bluedot_webhook(event_data: dict):
    # Pydantic's from_orm/model_validate doesn't handle aliased fields well from dict
    event_data["createdAt"] = event_data.pop("created_at")
    event_data["meetingId"] = event_data.pop("meeting_id")
    event_data["summaryV2"] = event_data.pop("summary_v2")
    event_data["videoId"] = event_data.pop("video_id")
    event = BluedotMeetingSummaryCreatedEvent.model_validate(event_data)

    for attendee_email in event.attendees:
        try:
            calendar_service = GoogleCalendarService(user_email=attendee_email)
            next_occurrence = calendar_service.find_recurring_event_next_occurrence(
                meeting_link=event.meeting_id,
                start_time=event.created_at,
            )

            if next_occurrence:
                reminder_time = next_occurrence - timedelta(hours=1)
                send_mattermost_reminder.apply_async(
                    args=[event.model_dump(by_alias=True)], eta=reminder_time
                )
                logger.info(
                    f"Scheduled reminder for {event.meeting_id} at {reminder_time} "
                    f"for attendees: {event.attendees}"
                )
                # Once we find the event in one person's calendar, we assume it's the same for all
                break
        except Exception as e:
            logger.error(f"Could not process calendar for {attendee_email}. Error: {e}")


@celery_app.task(name="send_mattermost_reminder")
def send_mattermost_reminder(event_data: dict):
    event = BluedotMeetingSummaryCreatedEvent.model_validate(event_data)
    try:
        mm = Driver(
            {
                "url": settings.mattermost_url,
                "token": settings.mattermost_token,
                "scheme": "https" if "https" in settings.mattermost_url else "http",
                "port": 443 if "https" in settings.mattermost_url else 80,
            }
        )
        mm.login()
        team = mm.teams.get_team_by_name(settings.mattermost_team_name)
        if not team:
            logger.error(
                f"Mattermost team '{settings.mattermost_team_name}' not found."
            )
            return

        user_ids = []
        for email in event.attendees:
            try:
                user = mm.users.get_user_by_email(email)
                user_ids.append(user["id"])
            except Exception:
                logger.warning(f"Could not find Mattermost user for email: {email}")

        if not user_ids:
            logger.error("No Mattermost users found to send reminder to.")
            return

        # Create a group message
        channel = mm.channels.create_group_message_channel(user_ids)

        message = (
            f"**Reminder for your upcoming meeting: `{event.title}`**\n\n"
            "Here is the summary of the last session to refresh your memory:\n\n"
            "---\n\n"
            f"{event.summary_v2}"
        )

        mm.posts.create_post(options={"channel_id": channel["id"], "message": message})
        logger.info(f"Sent group reminder to users: {user_ids} in Mattermost.")

    except Exception as e:
        logger.error(f"Failed to initialize Mattermost driver or send message: {e}")
