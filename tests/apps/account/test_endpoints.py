import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from appserver.app import app
from appserver.db import create_async_engine, create_session
from appserver.apps.account.endpoints import user_detail
from appserver.apps.account.models import User
from appserver.apps.calendar.models import Calendar
from sqlmodel import SQLModel


async def test_user_detail_successfully(db_session: AsyncSession):
    host_user = User(
        username="test-hostuser",
        password="test",
        email="test.hostuser@example.com",
        display_name="test",
        is_host=True,
    )
    db_session.add(host_user)
    await db_session.commit()
    result = await user_detail(host_user.username, db_session)
    assert result.username == host_user.username
    assert result.email == host_user.email
    assert result.display_name == host_user.display_name
    assert result.is_host == host_user.is_host


async def test_user_detail_not_found(db_session: AsyncSession):
    with pytest.raises(HTTPException) as exc_info:
        await user_detail(username="not_found", session=db_session)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


def test_user_detail_by_http_not_found(client: TestClient):
    # client = TestClient(app)
    response = client.get("/account/users/not_found")

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_user_detail_by_http(client: TestClient, db_session: AsyncSession):
    user = User(
        username="test",
        password="test",
        email="test@example.com",
        display_name="test",
        is_host=True,
    )
    db_session.add(user)
    await db_session.commit()

    # client = TestClient(app)
    response = client.get("/account/users/test")

    # assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == 1
    assert data["username"] == "test"
    assert data["email"] == "test@example.com"
    assert data["display_name"] == "test"
    assert data["is_host"] == True
    assert data["created_at"] is not None
    assert data["updated_at"] is not None


# dsn = "sqlite+aiosqlite:///./test.db"
# engine = create_async_engine(dsn)

# async def test_user_detail_for_real_user():
#     async with engine.begin() as conn:
#         await conn.run_sync(SQLModel.metadata.drop_all)
#         await conn.run_sync(SQLModel.metadata.create_all)

#     session_factory = create_session(engine)
#     async with session_factory() as session:
#         user = User(
#             username="test",
#             password="test",
#             email="test@example.com",
#             display_name="test",
#             is_host=True,
#         )
#         session.add(user)
#         await session.commit()

#     client = TestClient(app)

#     response = client.get(f"/account/users/{user.username}")
#     data = response.json()
#     assert data["username"] == "test"
#     assert data["email"] == "test@example.com"
#     assert data["display_name"] == "test"

#     response = client.get("/account/users/not_found")
#     assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_user_detail_for_real_user(client: TestClient, db_session: AsyncSession):
    user = User(
        username="test",
        password="test",
        email="test@example.com",
        display_name="test",
        is_host=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()

    # client = TestClient(app)
 
    response = client.get(f"/account/users/{user.username}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == user.username
    assert data["email"] == user.email
    assert data["display_name"] == user.display_name

    response = client.get("/account/users/not_found")
    assert response.status_code == status.HTTP_404_NOT_FOUND

