from typing import Annotated
from datetime import time, date

from pydantic import AwareDatetime, EmailStr, AfterValidator, model_validator
from sqlmodel import SQLModel, Field

from appserver.libs.collections.sort import deduplicate_and_sort


class CalendarOut(SQLModel):
    topics: list[str]
    description: str


class CalendarDetailOut(CalendarOut):
    host_id: int
    google_calendar_id: str
    created_at: AwareDatetime
    updated_at: AwareDatetime


Topics = Annotated[list[str], AfterValidator(deduplicate_and_sort)]

class CalendarCreateIn(SQLModel):
    topics: Topics = Field(min_length=1, description="게스트와 나눌 주제들")
    description: str = Field(min_length=1, description="게스트에게 보여 줄 설명")
    google_calendar_id: EmailStr = Field(description="Google Calendar ID")


class CalendarUpdateIn(SQLModel):
    topics: Topics | None = Field(
        default=None,
        min_length=1,
        description=">게스트와 나눌 주제들>"
    )
    description: str | None = Field(
        default=None,
        min_length=10,
        description=">게스트에게 보여 줄 설명"
    )
    google_calendar_id: EmailStr | None = Field(
        default=None,
        min_length=10,
        description="Google Calendar ID"
    )


def validate_weekdays(weekdays: list[int]) -> list[int]:
    weekday_range = range(7)
    for weekday in weekdays:
        if weekday not in weekday_range:
            raise ValueError(f"요일 값은 0부터 6까지의 값이어야 합니다. 현재 값: {weekday}")
    return weekdays

"""
AfterValidator는 Pydantic v2에서 기본 타입 검증이 끝난 뒤에 실행되는 커스텀 검증기
즉, 타입이 맞는지 먼저 확인한 다음, 값의 의미(도메인 규칙)를 검사할 때 쓴다.

Annotated + AfterValidator
1. list[int] → 기본 타입 검증
2. AfterValidator(validate_weekdays) → 커스텀 검증

AfterValidator vs model_validator
1. 단일 필드 vs 여러 필드 조합
2. 타임 검증 이후 vs 모델 전체 생성 이후
3. 값 자체의 의미 검증 vs 필드 간 관계 검증
"""
Weekdays = Annotated[list[int], AfterValidator(validate_weekdays)]


class TimeSlotCreateIn(SQLModel):
    start_time: time
    end_time: time
    weekdays: Weekdays

    @model_validator(mode="after")
    def validate_time_slot(self):
        if self.start_time >= self.end_time:
            raise ValueError("시작 시간은 종료 시간보다 빨라야 합니다.")
        return self


class TimeSlotOut(SQLModel):
    start_time: time
    end_time: time
    weekdays: list[int]
    created_at: AwareDatetime
    updated_at: AwareDatetime


class BookingCreateIn(SQLModel):
    when: date
    topic: str
    description: str
    time_slot_id: int


class BookingOut(SQLModel):
    id: int
    when: date
    topic: str
    description: str
    time_slot: TimeSlotOut
    created_at: AwareDatetime
    updated_at: AwareDatetime