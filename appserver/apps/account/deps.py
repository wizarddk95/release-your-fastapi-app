from typing import Annotated
from datetime import datetime, timezone, timedelta
from sqlmodel import select
from fastapi import Depends, Cookie, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from appserver.db import DbSessionDep
from .exceptions import InvalidTokenError, ExpiredTokenError, UserNotFoundError
from .models import User
from .constants import AUTH_TOKEN_COOKIE_NAME
from .utils import decode_token, ACCESS_TOKEN_EXPIRE_MINUTES


async def get_user(auth_token: str | None, db_session: AsyncSession) -> User | None:
    if not auth_token:
        return None

    try:
        decoded = decode_token(auth_token)
    except Exception as e:
        raise InvalidTokenError() from e

    expires_at = datetime.fromtimestamp(decoded["exp"], timezone.utc)
    now = datetime.now(timezone.utc)
    if now > expires_at:
        raise ExpiredTokenError()

    stmt = select(User).where(User.username == decoded["sub"])
    result = await db_session.execute(stmt)

    return result.scalar_one_or_none()


# 클라이언트가 보낸 HTTP 요청의 Cookie 헤더에서 값을 읽습니다.
# 서버가 설정한 쿠키를 클라이언트가 저장하고, 이후 요청에 포함시킵니다.
# FastAPI는 요청의 Cookie 헤더를 파싱해 Cookie(...)로 주입합니다.
async def get_current_user(
    auth_token: Annotated[str | None, Cookie(...)],
    db_session: DbSessionDep
):
    user = await get_user(auth_token, db_session) # 현재 db 세션을 통해 사용자 정보를 조회

    if user is None:
        raise UserNotFoundError()
    return user

CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def get_current_user_optional(
    db_session: DbSessionDep,
    auth_token: Annotated[str | None, Cookie()] = None,
):
    user = await get_user(auth_token, db_session)
    return user

CurrentUserOptionalDep = Annotated[User | None, Depends(get_current_user_optional)]