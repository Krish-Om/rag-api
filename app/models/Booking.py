from datetime import date, datetime, time
from typing import Optional
from enum import Enum
from sqlmodel import Field, SQLModel


class InterviewType(str, Enum):
    TECHNICAL = "technical"
    HR = "hr"
    PHONE = "phone"
    VIDEO = "video"
    ONSITE = "onsite"
    GENERAL = "general"


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Booking(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str
    booking_date: date
    booking_time: time
    session_id: str  # Reference to the Redis chat session

    # Enhanced fields for booking parser
    interview_type: InterviewType = Field(default=InterviewType.GENERAL)
    status: BookingStatus = Field(default=BookingStatus.PENDING)
    confidence_score: float = Field(default=0.0)
    extracted_text: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default=None)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            time: lambda v: v.isoformat(),
        }
