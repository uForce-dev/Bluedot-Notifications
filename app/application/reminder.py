from __future__ import annotations

from datetime import datetime

from app.domain.repositories import NotificationLogRepository
from app.interfaces.gateways import MattermostGateway


class ReminderService:
    def __init__(
        self,
        mm: MattermostGateway,
        logs: NotificationLogRepository,
    ) -> None:
        self.mm = mm
        self.logs = logs

    def send_reminder(
        self,
        user_email: str,
        title: str,
        meeting_link: str,
        meeting_time: datetime | None,
        summary: str | None = None,
    ) -> None:
        user = self.mm.get_user_by_email(user_email)
        user_id = user["id"]

        time_part = (
            f"⏰ Время: {meeting_time.strftime('%Y-%m-%d %H:%M')}"
            if meeting_time
            else ""
        )
        summary_part = f"\n\n---\n\n{summary}" if summary else ""
        message = (
            f"📅 **Напоминание о предстоящей встрече: [{title}]({meeting_link})** ({time_part})"
            f"{summary_part}"
        )

        try:
            self.mm.send_dm(user_id=user_id, message=message)
            self.logs.log_sent(
                recipient_email=user_email,
                recipient_user_id=user_id,
                meeting_name=title,
                meeting_link=meeting_link,
            )
        except Exception as e:
            self.logs.log_failed(
                recipient_email=user_email,
                recipient_user_id=user_id,
                meeting_name=title,
                meeting_link=meeting_link,
                error=str(e),
            )
