from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from typing import Annotated
from fastapi import Depends


def create_engine(dsn: str):
    return create_async_engine(
        dsn,
        echo=True,
    )


def create_session(async_engine: AsyncEngine|None = None, **kwargs):
    if async_engine is None:
        async_engine = create_engine()
    return async_sessionmaker(
        async_engine,
        expire_on_commit=False, # 커밋 이후에도 ORM 객체의 모든 속성 값 유지
        autoflush=False,        # 버전 2에서는 권장하지 않음 (True일 경우 쿼리 실행 전이나 트랜잭션 커밋 전 세션과 데이터베이스 상태를 동기화함)
        class_=AsyncSession,    # 세션 클래스를 확장한 커스텀 세션 클래스를 사용할 때 지정
        **kwargs,
    )


DSN = "sqlite+aiosqlite:///./local.db"          # db.py 파일이 있는 경로에 local.db 파일을 생성
engine = create_engine(DSN)                     # 비동기 엔진
async_session_factory = create_session(engine)  # 비동기 세션

# FastAPI에서 사용할 비동기 생성기(async generator)
async def use_session(): 
    async with async_session_factory() as session: # 세션 팩토리에서 세션 반환
        yield session # 세션 반환 (함수에 주입)


DbSessionDep = Annotated[AsyncSession, Depends(use_session)]



