from datetime import date, datetime, time

from sqlmodel import Field, Relationship, SQLModel


class Booking(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str
    booking_date: date
    booking_time: time
    session_id: str  # Refrencing to the Redis chat session
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            time: lambda v: v.isoformat(),
        }
