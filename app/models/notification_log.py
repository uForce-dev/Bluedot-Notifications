from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.db import Base


class NotificationLog(Base):
    __tablename__ = "bluedot_notifier__notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    recipient_email = Column(String(320), nullable=False, index=True)
    recipient_user_id = Column(String(128), nullable=True, index=True)
    meeting_name = Column(String(512), nullable=True)
    meeting_link = Column(String(1024), nullable=True)
    status = Column(String(32), nullable=False, default="sent")
    error = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=False), nullable=False, default=datetime.utcnow)
