import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from appserver.db import create_async_engine, create_session, use_session
from appserver.app import include_routers
from appserver.apps.account import models as account_models
from appserver.apps.calendar import models as calendar_models
from appserver.apps.account.utils import hash_password
from sqlmodel import SQLModel


# 각 테스트마다 깨끗한 DB 상태를 만들고, 테스트가 끝나면 흔적을 남기지 않는 것
@pytest.fixture(autouse=True) 
async def db_session():
    dsn = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(dsn)       # 비동기 엔진 생성 (테스트 동안의 사용할 DB 연결 진입점)
    async with engine.begin() as conn:      # DB 연결 컨텍스트 (하나의 connection 안에서 테이블 생성/삭제)
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
    
