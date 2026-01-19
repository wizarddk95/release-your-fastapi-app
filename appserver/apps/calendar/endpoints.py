from typing import Annotated

from fastapi import APIRouter, status, Query
from sqlmodel import select, and_, extract
from sqlalchemy.exc import IntegrityError

from appserver.apps.account.models import User
from appserver.apps.calendar.models import Calendar, TimeSlot
from appserver.db import DbSessionDep
from appserver.apps.account.deps import CurrentUserOptionalDep, CurrentUserDep
from .models import Booking
from .schemas import (
    CalendarCreateIn, CalendarDetailOut, CalendarOut, CalendarUpdateIn,
    TimeSlotOut, TimeSlotCreateIn, BookingCreateIn, BookingOut,
    SimpleBookingOut,
)
from .exceptions import (
    HostNotFoundError, CalendarNotFoundError, CalendarAlreadyExistsError,
    GuestPermissionError, TimeSlotOverLapError, TimeSlotNotFoundError,
)


router = APIRouter()


@router.get("/calendar/{host_username}", status_code=status.HTTP_200_OK)
async def host_calendar_detail(
    host_username: str,             
    user: CurrentUserOptionalDep,
    session: DbSessionDep,
) -> CalendarDetailOut | CalendarOut:
    """
    매개변수
    - host_username: 호스트 사용자의 username
    - user: 캘린더 정보를 요청하는 사용자
    - session: 데이터베이스 세션
    """
    stmt = select(User).where(User.username == host_username)
    result = await session.execute(stmt)
    host = result.scalar_one_or_none()
    if host is None:
        raise HostNotFoundError()

    stmt = select(Calendar).where(Calendar.host_id == host.id)
    result = await session.execute(stmt)
    calendar = result.scalar_one_or_none()
    if calendar is None:
        raise CalendarNotFoundError()


    if user is not None and user.id == host.id:
        return CalendarDetailOut.model_validate(calendar)

    return CalendarOut.model_validate(calendar)


@router.post(
    "/calendar",
    status_code=status.HTTP_201_CREATED,
    response_model=CalendarDetailOut
)
async def create_calendar(
    user: CurrentUserDep,
    session: DbSessionDep,
    payload: CalendarCreateIn
) -> CalendarDetailOut:
    if user.is_host is False:
        raise GuestPermissionError()

    calendar = Calendar(
        host_id=user.id,
        topics=payload.topics,
        description=payload.description,
        google_calendar_id=payload.google_calendar_id,
    )    

    session.add(calendar)
    try:
        await session.commit()
    except IntegrityError as e:
        raise CalendarAlreadyExistsError()

    return calendar


@router.patch(
    "/calendar",
    status_code=status.HTTP_200_OK,
    response_model=CalendarDetailOut,
)
async def update_calendar(
    user: CurrentUserDep,
    session: DbSessionDep,
    payload: CalendarUpdateIn,
) -> CalendarDetailOut:

    # 호스트가 아니면 캘린더를 수정할 수 없다.
    if not user.is_host:
        raise GuestPermissionError()

    # 사용자에게 캘린더가 없으면 HTTP 404 응답을 한다.
    if user.calendar is None:
        raise CalendarNotFoundError()

    # topics 값이 있으면 변경하고
    if payload.topics is not None:
        user.calendar.topics = payload.topics
    # description 값이 있으면 변경하고
    if payload.description is not None:
        user.calendar.description = payload.description
    # 구글 캘린더 ID 값이 있으면 변경하고
    if payload.google_calendar_id is not None:
        user.calendar.google_calendar_id = payload.google_calendar_id

    await session.commit()

    return user.calendar


@router.post(
    "/time-slots",
    status_code=status.HTTP_201_CREATED,
    response_model=TimeSlotOut,
)
async def create_time_slot(
    user: CurrentUserDep,
    session: DbSessionDep,
    payload: TimeSlotCreateIn
) -> TimeSlotOut:
    if not user.is_host:
        raise GuestPermissionError()

    # 이미 존재하는 타임슬롯과 겹치는지 확인
    # and_ 연산자 사용 방법
    stmt = select(TimeSlot).where(
        and_(
            TimeSlot.calendar_id == user.calendar.id,
            TimeSlot.start_time < payload.end_time,
            TimeSlot.end_time > payload.start_time,
        )
    )

    # # & 연산자 사용 방법
    # stmt = select(TimeSlot).where(
    #     (TimeSlot.calendar_id == user.calendar.id) &
    #     (TimeSlot.start_time < payload.end_time) &
    #     (TimeSlot.end_time > payload.start_time)
    # )

    result = await session.execute(stmt)
    existing_time_slots = result.scalars().all()

    for existing_time_slot in existing_time_slots:
        if any(day in existing_time_slot.weekdays for day in payload.weekdays):
            raise TimeSlotOverLapError()

    time_slot = TimeSlot(
        calendar_id=user.calendar.id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        weekdays=payload.weekdays,
    )
    session.add(time_slot)
    await session.commit()
    return time_slot


@router.post(
    "/bookings/{host_username}",
    status_code=status.HTTP_201_CREATED,
    response_model=BookingOut,
)
async def create_booking(
    host_username: str,
    user: CurrentUserDep,
    session: DbSessionDep,
    payload: BookingCreateIn
) -> BookingOut:
    stmt = (
        select(User)
        .where(User.username == host_username)
        .where(User.is_host.is_(True)) # is_는 동등성 비교, 간단히 말해 등호 비교를 하는 데 사용합니다.
    )
    result = await session.execute(stmt)
    host = result.scalar_one_or_none()

    if host is None or host.calendar is None:
        raise HostNotFoundError()

    stmt = (
        select(TimeSlot)
        .where(TimeSlot.id == payload.time_slot_id)
        .where(TimeSlot.calendar_id == host.calendar.id)
    )
    result = await session.execute(stmt)
    time_slot = result.scalar_one_or_none()

    if time_slot is None:
        raise TimeSlotNotFoundError()
    if payload.when.weekday() not in time_slot.weekdays:
        raise TimeSlotNotFoundError()

    booking = Booking(
        guest_id=user.id,
        when=payload.when,
        topic=payload.topic,
        description=payload.description,
        time_slot_id=payload.time_slot_id,
    )
    session.add(booking)
    await session.commit()
    await session.refresh(booking)
    
    return booking


@router.get(
    "/bookings",
    status_code=status.HTTP_200_OK,
    response_model=list[BookingOut],
)
async def get_host_bookings_by_month(
    user: CurrentUserDep,
    session: DbSessionDep,
    page: Annotated[int, Query(ge=1)],
    page_size: Annotated[int, Query(ge=1, le=50)]
) -> list[BookingOut]:
    if not user.is_host or user.calendar is None:
        raise HostNotFoundError()
    stmt = (
        select(Booking)
        .where(Booking.time_slot.has(TimeSlot.calendar_id == user.calendar.id))
        .order_by(Booking.when.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get(
    "/calendar/{host_username}/bookings",
    status_code=status.HTTP_200_OK,
    response_model=list[SimpleBookingOut]
)
async def host_calendar_bookings(
    host_username: str,
    session: DbSessionDep,
    year: Annotated[int, Query(ge=2024, le=2025)],
    month: Annotated[int, Query(ge=1, le=12)],
) -> list[SimpleBookingOut]:
    stmt = select(User).where(User.username == host_username)
    result = await session.execute(stmt)
    host = result.scalar_one_or_none()
    if host is None or host.calendar is None:
        raise HostNotFoundError()

    stmt = (
        select(Booking)
        .where(Booking.time_slot.has(TimeSlot.calendar_id == host.calendar.id))
        .where(extract('year', Booking.when) == year)
        .where(extract('month', Booking.when) == month)
        .order_by(Booking.when.desc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()