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
    def __init__(self, user_email: str) -> None:
        self.user_email = user_email
        self.service = None
        try:
            creds = service_account.Credentials.from_service_account_file(
                settings.google_service_account_file, scopes=SCOPES
            )
            delegated_credentials = creds.with_subject(user_email)
            self.service = build("calendar", "v3", credentials=delegated_credentials)
        except Exception:
            logger.exception("Failed to initialize Google Calendar service")

    def is_ready(self) -> bool:
        return self.service is not None

    def find_recurring_event_next_occurrence(
        self, meeting_link: str, start_time: datetime
    ) -> tuple[str, str, datetime] | None:
        if not self.is_ready():
            return None

        event = self._find_event_by_link(meeting_link, start_time)
        if not event:
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
            return None

        event_start_str = event["start"].get("dateTime")
        event_start = datetime.fromisoformat(event_start_str)

        rrule_str = next((r for r in recurrence if r.startswith("RRULE:")), None)
        if not rrule_str:
            return None

        rules = rrulestr(rrule_str, dtstart=event_start)
        next_occurrence = rules.after(event_start)

        return event["summary"], event["htmlLink"], next_occurrence

    def _find_event_by_link(
        self, meeting_link: str, search_time: datetime
    ) -> dict | None:
        time_min = (search_time - timedelta(hours=12)).isoformat()
        time_max = (search_time + timedelta(hours=12)).isoformat()

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
            events = events_result.get("items", [])

            for event in events:
                if event.get("hangoutLink") == meeting_link:
                    return event

            return None

        except HttpError:
            logger.exception("HTTP error fetching calendar")
            return None
        except Exception:
            logger.exception("Unexpected error fetching calendar events")
            return None
