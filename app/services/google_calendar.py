import logging
from datetime import datetime, timedelta

from dateutil.rrule import rrulestr
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


class GoogleCalendarService:
    def __init__(self, user_email: str):
        self.user_email = user_email
        self.service = None
        try:
            creds = service_account.Credentials.from_service_account_file(
                settings.google_service_account_file, scopes=SCOPES
            )
            delegated_credentials = creds.with_subject(user_email)
            self.service = build("calendar", "v3", credentials=delegated_credentials)
        except FileNotFoundError:
            logger.error(
                f"Service account file not found at: {settings.google_service_account_file}"
            )
        except Exception as e:
            logger.error(
                f"Failed to initialize Google Calendar service for {user_email}: {e}"
            )

    def is_ready(self) -> bool:
        return self.service is not None

    def find_recurring_event_next_occurrence(
        self, meeting_link: str, start_time: datetime
    ) -> datetime | None:
        print(f"start_time: {start_time}")
        if not self.is_ready():
            return None

        event = self._find_event_by_link(meeting_link, start_time)
        logger.info(f"Event found: {event}")
        if not event:
            logger.warning(
                f"No calendar event found for link '{meeting_link}' "
                f"in calendar of '{self.user_email}'"
            )
            return None

        recurrence = event.get("recurrence")
        if not recurrence and event.get("recurringEventId"):
            parent_id = event["recurringEventId"]
            parent_event = (
                self.service.events()
                .get(calendarId="primary", eventId=parent_id)
                .execute()
            )
            recurrence = parent_event.get("recurrence")

        if not recurrence:
            logger.info(f"Meeting {meeting_link} is not a recurring event.")
            return None

        event_start_str = event["start"].get("dateTime")
        event_start = datetime.fromisoformat(event_start_str)

        rrule_str = next((r for r in recurrence if r.startswith("RRULE:")), None)
        if not rrule_str:
            logger.warning("No RRULE found in recurrence.")
            return None

        rules = rrulestr(rrule_str, dtstart=event_start)
        next_occurrence = rules.after(event_start)

        if next_occurrence:
            logger.info(f"Next meeting for {meeting_link} is at {next_occurrence}")

        return next_occurrence

    def _find_event_by_link(
        self, meeting_link: str, search_time: datetime
    ) -> dict | None:
        time_min = (search_time - timedelta(hours=12)).isoformat()
        time_max = (search_time + timedelta(hours=12)).isoformat()

        logger.debug(
            f"Searching calendar for {self.user_email} between {time_min} and {time_max}"
        )
        print(
            f"Searching calendar for {self.user_email} between {time_min} and {time_max}"
        )

        try:
            events_result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            print(f"events_result: {events_result}")
            events = events_result.get("items", [])

            for event in events:
                if event.get("hangoutLink") == meeting_link:
                    return event

            return None

        except HttpError as e:
            logger.error(
                f"HTTP error fetching calendar for {self.user_email}. "
                f"Status: {e.resp.status}, Reason: {e.reason}, URL: {e.uri}, Body: {e.content.decode()}"
            )
            return None
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while fetching Google Calendar events for {self.user_email}: {e}",
                exc_info=True,
            )
            return None
