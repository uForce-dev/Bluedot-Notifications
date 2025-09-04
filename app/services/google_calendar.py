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
            self.service = None
        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar service: {e}")
            self.service = None

    def find_recurring_event_next_occurrence(
        self, meeting_link: str, start_time: datetime
    ) -> datetime | None:
        if not self.service:
            return None

        event = self._find_event_by_link(meeting_link, start_time)
        if not event:
            logger.warning(
                f"No calendar event found for link '{meeting_link}' "
                f"in calendar of '{self.user_email}'"
            )
            return None

        recurrence = event.get("recurrence")
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
        next_occurrence = rules.after(start_time)

        logger.info(f"Next meeting for {meeting_link} is at {next_occurrence}")
        return next_occurrence

    def _find_event_by_link(
        self, meeting_link: str, search_time: datetime
    ) -> dict | None:
        time_min = (search_time - timedelta(hours=12)).isoformat() + "Z"
        time_max = (search_time + timedelta(hours=12)).isoformat() + "Z"

        try:
            events_result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=time_min,
                    timeMax=time_max,
                    q=meeting_link.split("/")[-1], # Search by meeting code for better accuracy
                    singleEvents=True,
                )
                .execute()
            )
            events = events_result.get("items", [])
            for event in events:
                if event.get("hangoutLink") == meeting_link:
                    return event
            return None
        except HttpError as e:
            logger.error(
                f"HTTP error fetching calendar for {self.user_email}: {e.content}"
            )
            return None
        except Exception as e:
            logger.error(f"Error fetching Google Calendar events: {e}")
            return None
