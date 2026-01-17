from datetime import timezone, datetime, date, time
from typing import TYPE_CHECKING
from pydantic import AwareDatetime
from sqlalchemy_utc import UtcDateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field, Relationship, Text, JSON, func, String, Column
if TYPE_CHECKING:
    from appserver.apps.account.models import User


class Calendar(SQLModel, table=True):
    __tablename__ = "calendars"

    id: int = Field(default=None, primary_key=True)
    # 문자열 항목으로 갖는 리스트형 객체 → 데이터베이스에서 JSON 자료형으로 다룹니다.
    # topics: list[str] = Field(sa_type=JSON, default_factory=list, description="게스트와 나눌 주제들")
    # DB가 PostgreSQL이면 JSONB, 그 외에는 JSON으로 다룹니다.
    topics: list[str] = Field(sa_type=JSON().with_variant(JSONB(astext_type=Text()), "postgresql"), description="게스트와 나눌 주제들")
    description: str = Field(sa_type=Text, description="게스트에게 보여 줄 설명")
    google_calendar_id: str = Field(max_length=1024, description="Google Calendar ID")
    created_at: AwareDatetime = Field(
        default=None,
        nullable=False,
        sa_type=UtcDateTime,
        sa_column_kwargs={
            "server_default": func.now(),
        }
    )
    updated_at: AwareDatetime = Field(
        default=None,
        nullable=False,
        sa_type=UtcDateTime,
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": lambda: datetime.now(timezone.utc),
        }
    )   

    host_id: int = Field(foreign_key="users.id", unique=True)
    host: "User" = Relationship(
        back_populates="calendar",
        sa_relationship_kwargs={"uselist": False, "single_parent": True},
    )
    time_slots: list["TimeSlot"] = Relationship(back_populates="calendar")


class TimeSlot(SQLModel, table=True):
    __tablename__ = "time_slots"

    id: int = Field(default=None, primary_key=True)
    start_time: time
    end_time: time
    weekdays: list[int] = Field(
        sa_type=JSON().with_variant(JSONB(astext_type=Text()), "postgresql"),
        description="예약 가능한 요일들"
    )
    created_at: AwareDatetime = Field(
        default=None,
        nullable=False,
        sa_type=UtcDateTime,
        sa_column_kwargs={
            "server_default": func.now(),
        }
    )
    updated_at: AwareDatetime = Field(
        default=None,
        nullable=False,
        sa_type=UtcDateTime,
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": lambda: datetime.now(timezone.utc),
        }
    )   

    calendar_id: int = Field(foreign_key="calendars.id")
    calendar: Calendar = Relationship(back_populates="time_slots")

    bookings: list["Booking"] = Relationship(back_populates="time_slot")


class Booking(SQLModel, table=True):
    __tablename__ = "bookings"

    id: int = Field(default=None, primary_key=True)
    when: date
    topic: str
    description: str = Field(sa_type=Text, description="예약 설명")
    created_at: AwareDatetime = Field(
        default=None,
        nullable=False,
        sa_type=UtcDateTime,
        sa_column_kwargs={
            "server_default": func.now(),
        }
    )
    updated_at: AwareDatetime = Field(
        default=None,
        nullable=False,
        sa_type=UtcDateTime,
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": lambda: datetime.now(timezone.utc),
        }
    )   

    time_slot_id: int = Field(foreign_key="time_slots.id")
    time_slot: TimeSlot = Relationship(back_populates="bookings")

    guest_id: int = Field(foreign_key="users.id")
    guest: "User" = Relationship(back_populates="bookings")


