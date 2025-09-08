from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class BluedotMeetingSummaryCreatedEvent(BaseModel):
    attendees: list[str]
    created_at: datetime = Field(alias="createdAt")
    meeting_id: str = Field(alias="meetingId")
    summary: str
    summary_v2: str = Field(alias="summaryV2")
    title: str
    type: str
    video_id: str = Field(alias="videoId")

    @field_validator("attendees", mode="before")
    def normalize_attendees(cls, v):
        normalized = []
        for item in v:
            if isinstance(item, str):
                normalized.append(item)
            elif isinstance(item, dict) and "email" in item:
                normalized.append(item["email"])
            else:
                raise ValueError(f"Unsupported attendee format: {item}")
        return normalized

    @property
    def meeting_link(self) -> str:
        if self.meeting_id.startswith("http"):
            return self.meeting_id
        return f"https://{self.meeting_id}"
