from typing import Annotated
from datetime import datetime, timezone, timedelta
from sqlmodel import select
from fastapi import Depends, Cookie, HTTPException, status
from appserver.db import DbSessionDep
from .exceptions import InvalidTokenError, ExpiredTokenError, UserNotFoundError
from .models import User
from .constants import AUTH_TOKEN_COOKIE_NAME
from .utils import decode_token, ACCESS_TOKEN_EXPIRE_MINUTES

async def get_current_user(
    auth_token: Annotated[str | None, Cookie(...)],
    db_session: DbSessionDep
):

    # 테스트 안정성을 위한 코드
    # - get_current_user 함수는 FastAPI DI 컨텍스트 밖에서도 호출될 수 있으므로
    # - 아래처럼 자체 방어 로직을 가지는 게 안전하다.
    if auth_token is None:
        raise InvalidTokenError()

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
    user = result.scalar_one_or_none()

    if user is None:
        raise UserNotFoundError()

    return user
    

CurrentUserDep = Annotated[User, Depends(get_current_user)]
