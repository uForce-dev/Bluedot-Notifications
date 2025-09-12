from __future__ import annotations

from datetime import datetime
from typing import Protocol, Optional


class NotificationLogRepository(Protocol):
    def log_sent(
        self,
        recipient_email: str,
        recipient_user_id: Optional[str],
        notification_type: str,
        meeting_name: Optional[str],
        meeting_link: Optional[str],
        occurrence_at: Optional[datetime] = None,
    ) -> None: ...

    def log_failed(
        self,
        recipient_email: str,
        notification_type: str,
        meeting_name: Optional[str],
        meeting_link: Optional[str],
        error: str,
        occurrence_at: Optional[datetime] = None,
        recipient_user_id: Optional[str] = None,
    ) -> None: ...

    def exists_sent(
        self,
        recipient_email: str,
        notification_type: str,
        meeting_link: str,
        occurrence_at: Optional[datetime] = None,
    ) -> bool: ...
