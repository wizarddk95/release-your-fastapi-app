from fastapi import APIRouter, status
from sqlmodel import select
from appserver.apps.account.models import User
from appserver.apps.calendar.models import Calendar
from appserver.db import DbSessionDep
from appserver.apps.account.deps import CurrentUserOptionalDep
from .schemas import CalendarDetailOut, CalendarOut
from .exceptions import HostNotFoundError, CalendarNotFoundError


router = APIRouter(prefix="/calendar")


@router.get("/{host_username}", status_code=status.HTTP_200_OK)
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


