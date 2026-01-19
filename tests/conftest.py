import pytest
import calendar
from datetime import time, date

from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from appserver.db import create_async_engine, create_session, use_session
from appserver.app import include_routers
from appserver.apps.account import models as account_models
from appserver.apps.calendar import models as calendar_models
from appserver.apps.account.utils import hash_password
from appserver.apps.account.schemas import LoginPayload
from sqlmodel import SQLModel


# 각 테스트마다 깨끗한 DB 상태를 만들고, 테스트가 끝나면 흔적을 남기지 않는 것
@pytest.fixture(autouse=True) # autouse=True → 각 테스트 함수 실행 시 자동으로 픽스터가 **한 번** 실행됩니다.
async def db_session():
    dsn = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(dsn)       # 비동기 엔진 생성 (테스트 동안의 사용할 DB 연결 진입점)
    async with engine.begin() as conn:      # DB 연결 컨텍스트 (하나의 connection 안에서 테이블 생성/삭제)
        # SQALModel.metadata.(...)() 함수들은 동기 SQLAlchemy API.
        # 비동기 컨텍스트에서 동기 전용 함수를 사용할 때는 conn.run_sync() 함수를 사용해야 한다.
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all) 

        session_factory = create_session(engine) # 엔진과 바인딩된 sessionmaker 생성
        async with session_factory() as session: 
            # 테스트 함수에게 session을 넘겨줌
            # yield 이전 → setup
            yield session
            # yield 이후 → teardown
        
        # await conn.rollback() 
        await conn.run_sync(SQLModel.metadata.drop_all)
        
    await engine.dispose() # 커넥션 풀 정리 


@pytest.fixture()
def fastapi_app(db_session: AsyncSession):
    app = FastAPI()       
    include_routers(app)  

    async def override_use_session():
        yield db_session

    app.dependency_overrides[use_session] = override_use_session # 의존성 오버라이드
    return app


@pytest.fixture()
def client(fastapi_app: FastAPI):
    with TestClient(fastapi_app) as client:
        yield client


@pytest.fixture()
async def host_user(db_session: AsyncSession):
    user = account_models.User(
        username="puddingcamp",
        hashed_password=hash_password("testtest"),
        email="puddingcamp@example.com",
        display_name="푸딩캠프",
        is_host=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    return user
    

@pytest.fixture()
def client_with_auth(fastapi_app: FastAPI, host_user: account_models.User):
    payload = LoginPayload.model_validate({
        "username": host_user.username, # "puddingcamp"
        "password": "testtest",
    })

    # TestClient가 ASGI 앱을
    # - 내부적으로 httpx + anyio로 감싸서 **실제 서버 띄우지 않고도**
    # - Get /health 같은 요청을 보낼 수 있게 만듭니다. 
    # - 실제 네트워크를 타지 않으며 메모리 내부에서 FastAPI 앱으로 바로 전달됩니다.
    with TestClient(fastapi_app) as client:

        # 자동으로 LoginPayload로 변환됩니다.
        # FastAPI가 이걸 요청 처리 파이프라인에서 보장해줍니다.
        # 타입 힌트 확인(payload: LoginPayload) → Pydantic으로 검증 + 변환
        response = client.post("/account/login", json=payload.model_dump())
        assert response.status_code == status.HTTP_200_OK

        auth_token = response.cookies.get("auth_token")
        assert auth_token is not None

        # client.cookies["auth_token"] = auth_token
        client.cookies.set("auth_token", auth_token)
        yield client # 인증을 받은 클라이언트 반환


@pytest.fixture()
async def guest_user(db_session: AsyncSession):
    user = account_models.User(
        username="puddingcafe",
        hashed_password=hash_password("testtest"),
        email="puddingcafe@example.com",
        display_name="푸딩카페",
        is_host=False,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    return user


@pytest.fixture()
async def host_user_calendar(db_session: AsyncSession, host_user: account_models.User):
    calendar = calendar_models.Calendar(
        host_id=host_user.id,
        description="푸딩캠프 캘린더입니다.",
        topics=["푸딩캠프", "푸딩캠프2"],
        google_calendar_id="1234567890",
    )
    db_session.add(calendar)
    await db_session.flush()
    await db_session.commit()
    await db_session.refresh(host_user)
    return calendar


@pytest.fixture()
def client_with_guest_auth(fastapi_app: FastAPI, guest_user: account_models.User):
    payload = LoginPayload.model_validate({
        "username": guest_user.username, # puddingcafe
        "password": "testtest",
    })

    with TestClient(fastapi_app) as client:
        response = client.post("/account/login", json=payload.model_dump())
        assert response.status_code == status.HTTP_200_OK

        auth_token = response.cookies.get("auth_token")
        assert auth_token is not None

        client.cookies.set("auth_token", auth_token)
        yield client


@pytest.fixture()
async def time_slot_tuesday(
    db_session: AsyncSession,
    host_user_calendar: calendar_models.Calendar,
):
    time_slot = calendar_models.TimeSlot(
        start_time=time(9, 0),
        end_time=time(10, 0),
        weekdays=[calendar.TUESDAY],
        calendar_id=host_user_calendar.id,
    )
    db_session.add(time_slot)
    await db_session.commit()
    return time_slot


@pytest.fixture()
async def cute_guest_user(db_session: AsyncSession):
    user = account_models.User(
        username="cuteguest",
        hashed_password=hash_password("testtest"),
        email="cute_guest@example.com",
        display_name="귀여운 게스트",
        is_host=False,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    return user


@pytest.fixture()
async def charming_host_user(db_session: AsyncSession):
    user = account_models.User(
        username="charming_host",
        hashed_password=hash_password("testtest"),
        email="charming_host@example.com",
        display_name="매력 있는 캠프",
        is_host=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    return user


@pytest.fixture()
async def charming_host_calendar(db_session: AsyncSession, charming_host_user: account_models.User):
    calendar = calendar_models.Calendar(
        host_id=charming_host_user.id,
        description="매력 있는 캠프 캘린더입니다.",
        topics=["매력 있는 캠프", "매력 있는 캠프2"],
        google_calendar_id="0987654321",
    )
    db_session.add(calendar)
    await db_session.commit()
    await db_session.refresh(charming_host_user)
    return calendar


@pytest.fixture()
async def time_slot_wednesday_thursday(
    db_session: AsyncSession,
    charming_host_calendar: calendar_models.Calendar,
):
    time_slot = calendar_models.TimeSlot(
        start_time=time(10, 0),
        end_time=time(11, 0),
        weekdays=[calendar.WEDNESDAY, calendar.THURSDAY],
        calendar_id=charming_host_calendar.id,
    )
    db_session.add(time_slot)
    await db_session.commit()
    return time_slot


@pytest.fixture()
async def host_bookings(
    db_session: AsyncSession,
    guest_user: account_models.User,
    time_slot_tuesday: calendar_models.TimeSlot,
):
    bookings = []
    for when in [date(2024, 12, 3), date(2024, 12, 10), date(2024, 12, 17), date(2025, 1, 7)]:
        booking = calendar_models.Booking(
            when=when,
            topic="test",
            description="test",
            time_slot_id=time_slot_tuesday.id,
            guest_id=guest_user.id,
        )
        db_session.add(booking)
        bookings.append(booking)
    await db_session.commit()
    return bookings


@pytest.fixture()
async def charming_host_bookings(
    db_session: AsyncSession,
    guest_user: account_models.User,
    time_slot_wednesday_thursday: calendar_models.TimeSlot,
):
    bookings = []
    for when in [date(2024, 12, 4), date(2024, 12, 5), date(2024, 12, 11)]:
        booking = calendar_models.Booking(
            when=when,
            topic="test",
            description="test",
            time_slot_id=time_slot_wednesday_thursday.id,
            guest_id=guest_user.id,
        )
        db_session.add(booking)
        bookings.append(booking)
    
    await db_session.commit()
    return bookings

