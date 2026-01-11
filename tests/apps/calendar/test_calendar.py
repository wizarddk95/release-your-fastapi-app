import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from appserver.apps.account.models import User
from appserver.apps.calendar.models import Calendar
from appserver.apps.calendar.schemas import CalendarDetailOut, CalendarOut
from appserver.apps.calendar.endpoints import host_calendar_detail
from appserver.apps.calendar.exceptions import HostNotFoundError, CalendarNotFoundError


@pytest.mark.parametrize("user_key, expected_type", [
    ("host_user", CalendarDetailOut),   # 1. 호스트 유저 
    ("guest_user", CalendarOut),        # 2. 게스트 유저
    (None, CalendarOut),                # 3. 로그인하지 않은 유저
])
async def test_호스트인_사용자의_username_으로_캘린더_정보를_가져온다(
    user_key: str | None,
    expected_type: type[CalendarOut | CalendarDetailOut],
    host_user: User,
    host_user_calendar: Calendar,
    guest_user: User,
    db_session: AsyncSession,
):
    users = {
        "host_user": host_user,
        "guest_user": guest_user,
        None: None,
    }
    user = users[user_key]

    result = await host_calendar_detail(host_user.username, user, db_session)

    assert isinstance(result, expected_type)
    result_keys = frozenset(result.model_dump().keys())
    expected_keys = frozenset(expected_type.model_fields.keys())
    assert result_keys == expected_keys

    assert result.topics == host_user_calendar.topics
    assert result.description == host_user_calendar.description
    if isinstance(result, CalendarDetailOut):
        assert result.google_calendar_id == host_user_calendar.google_calendar_id


async def test_존재하지_않는_사용자의_username_으로_캘린더_정보를_가져오려_하면_404_응답을_반환한다(
    db_session: AsyncSession,
):
    with pytest.raises(HostNotFoundError):
        await host_calendar_detail(host_username="not_exist_user", user=None, session=db_session)


async def test_호스트_유저가_아닌_유저가_캘린더_정보를_가져오려_하면_404_응답을_반환한다(
    guest_user: User,
    db_session: AsyncSession,
):
    with pytest.raises(CalendarNotFoundError):
        await host_calendar_detail(guest_user.username, guest_user, db_session)

        