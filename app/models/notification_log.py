from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint

from app.db import Base


class NotificationLog(Base):
    __tablename__ = "bluedot_notifier__notification_logs"
    __table_args__ = (
        UniqueConstraint(
            "notification_type",
            "recipient_email",
            "meeting_link",
            "occurrence_at",
            name="uq_notification_reminder_occurrence",
        ),
        UniqueConstraint(
            "notification_type",
            "recipient_email",
            "video_id",
            name="uq_notification_summary_video",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    recipient_email = Column(String(320), nullable=False, index=True)
    recipient_user_id = Column(String(128), nullable=True, index=True)
    notification_type = Column(String(32), nullable=False, default="reminder")
    meeting_name = Column(String(512), nullable=True)
    meeting_link = Column(String(1024), nullable=True)
    video_id = Column(String(128), nullable=True, index=True)
    occurrence_at = Column(DateTime(timezone=False), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="sent")
    error = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=False), nullable=False, default=datetime.utcnow)
