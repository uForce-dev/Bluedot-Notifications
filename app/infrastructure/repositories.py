from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.domain.repositories import NotificationLogRepository
from app.models import NotificationLog


class SQLAlchemyNotificationLogRepository(NotificationLogRepository):
    def __init__(self, db: Session) -> None:
        self.db = db

    def log_sent(
        self,
        recipient_email: str,
        recipient_user_id: Optional[str],
        notification_type: str,
        meeting_name: Optional[str],
        meeting_link: Optional[str],
    ) -> None:
        self.db.add(
            NotificationLog(
                recipient_email=recipient_email,
                recipient_user_id=recipient_user_id,
                notification_type=notification_type,
                meeting_name=meeting_name,
                meeting_link=meeting_link,
                status="sent",
            )
        )
        self.db.commit()

    def log_failed(
        self,
        recipient_email: str,
        notification_type: str,
        meeting_name: Optional[str],
        meeting_link: Optional[str],
        error: str,
        recipient_user_id: Optional[str] = None,
    ) -> None:
        self.db.add(
            NotificationLog(
                recipient_email=recipient_email,
                recipient_user_id=recipient_user_id,
                notification_type=notification_type,
                meeting_name=meeting_name,
                meeting_link=meeting_link,
                status="failed",
                error=error,
            )
        )
        self.db.commit()
