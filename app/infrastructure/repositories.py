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
        occurrence_at: Optional[datetime] = None,
    ) -> None:
        self.db.add(
            NotificationLog(
                recipient_email=recipient_email,
                recipient_user_id=recipient_user_id,
                notification_type=notification_type,
                meeting_name=meeting_name,
                meeting_link=meeting_link,
                occurrence_at=occurrence_at,
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
        occurrence_at: Optional[datetime] = None,
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
                occurrence_at=occurrence_at,
                status="failed",
                error=error,
            )
        )
        self.db.commit()

    def exists_sent(
        self,
        recipient_email: str,
        notification_type: str,
        meeting_link: str,
        occurrence_at: Optional[datetime] = None,
    ) -> bool:
        query = (
            self.db.query(NotificationLog)
            .filter(
                NotificationLog.recipient_email == recipient_email,
                NotificationLog.notification_type == notification_type,
                NotificationLog.meeting_link == meeting_link,
                NotificationLog.status == "sent",
            )
        )
        if occurrence_at is not None:
            query = query.filter(NotificationLog.occurrence_at == occurrence_at)
        return query.first() is not None
