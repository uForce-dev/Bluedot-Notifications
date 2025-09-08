from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.domain.repositories import NotificationLogRepository
from app.interfaces.gateways import MattermostGateway
from app.core.config import settings


tz = ZoneInfo(settings.timezone)


class ReminderService:
    def __init__(
        self,
        mm: MattermostGateway,
        logs: NotificationLogRepository,
    ) -> tuple[str, str] | None:
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

        tz = ZoneInfo(settings.timezone)
        if meeting_time:
            src = (
                meeting_time
                if meeting_time.tzinfo
                else meeting_time.replace(tzinfo=ZoneInfo("UTC"))
            )
            mt_local = src.astimezone(tz)
            time_part = mt_local.strftime("%d.%m.%Y %H:%M %Z")
        else:
            time_part = ""
        summary_part = f"\n\n---\n\n{summary}" if summary else ""
        message = (
            f"📅 **Регулярная встреча: [{title}]({meeting_link})**\n\n"
            f"⏰ Следующая встреча состоится {time_part}.\n\n"
            f"Перед встречей предлагаем ознакомиться с саммари предыдущей:\n\n"
            f"{summary_part}"
        )

        try:
            root_post_id, channel_id = self.mm.send_dm(user_id=user_id, message=message)
            self.logs.log_sent(
                recipient_email=user_email,
                recipient_user_id=user_id,
                notification_type="reminder",
                meeting_name=title,
                meeting_link=meeting_link,
            )
        except Exception as e:
            self.logs.log_failed(
                recipient_email=user_email,
                notification_type="reminder",
                recipient_user_id=user_id,
                meeting_name=title,
                meeting_link=meeting_link,
                error=str(e),
            )
        return (root_post_id, channel_id)

    def send_summary_ready(
        self,
        user_email: str,
        title: str,
        meeting_link: str,
        summary: str,
        reminder_time: datetime | None = None,
    ) -> tuple[str, str] | None:
        user = self.mm.get_user_by_email(user_email)
        user_id = user["id"]

        if reminder_time:
            src = (
                reminder_time
                if reminder_time.tzinfo
                else reminder_time.replace(tzinfo=ZoneInfo("UTC"))
            )
            rt_local = src.astimezone(tz)
            reminder_note = f"\n\n🔔 Я напомню тебе об этом саммари перед следующей встречей, в {rt_local.strftime('%d.%m.%Y %H:%M %Z')}"
        else:
            reminder_note = ""
        message = (
            f"📝 **Готово краткое содержание встречи: [{title}]({meeting_link})**\n"
            f"{reminder_note}\n\n"
            f"---\n\n{summary}"
        )

        try:
            root_post_id, channel_id = self.mm.send_dm(user_id=user_id, message=message)
            self.logs.log_sent(
                recipient_email=user_email,
                recipient_user_id=user_id,
                notification_type="summary",
                meeting_name=title,
                meeting_link=meeting_link,
            )
        except Exception as e:
            self.logs.log_failed(
                recipient_email=user_email,
                notification_type="summary",
                recipient_user_id=user_id,
                meeting_name=title,
                meeting_link=meeting_link,
                error=str(e),
            )
        return (root_post_id, channel_id)

    def reply_reminder_in_thread(
        self,
        root_post_id: str,
        channel_id: str,
        user_email: str,
        title: str,
        meeting_link: str,
        meeting_time: datetime | None,
    ) -> None:
        tz = ZoneInfo(settings.timezone)
        if meeting_time:
            src = (
                meeting_time
                if meeting_time.tzinfo
                else meeting_time.replace(tzinfo=ZoneInfo("UTC"))
            )
            mt_local = src.astimezone(tz)
            time_part = mt_local.strftime("%d.%m.%Y %H:%M %Z")
        else:
            time_part = ""
        message = (
            f"<@{user_email}> 📅 Привет! У тебя регулярная встреча [{title}]({meeting_link}) в {time_part}.\n"
            f"Можешь взглянуть на саммари прошлой встречи перед началом."
        )
        self.mm.reply_in_thread(
            root_post_id=root_post_id, channel_id=channel_id, message=message
        )
