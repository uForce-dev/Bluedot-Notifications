from datetime import datetime

from pydantic import BaseModel, Field


class BluedotMeetingSummaryCreatedEvent(BaseModel):
    attendees: list[str]
    created_at: datetime = Field(alias="createdAt")
    meeting_id: str = Field(alias="meetingId")
    summary: str
    summary_v2: str = Field(alias="summaryV2")
    title: str
    type: str
    video_id: str = Field(alias="videoId")
