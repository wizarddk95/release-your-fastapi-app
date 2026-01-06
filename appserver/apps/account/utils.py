from datetime import datetime, timedelta, timezone
from jose import jwt
from typing import Any, Union
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def hash_password(password: str) -> str:
    """
    인자로 주어진 문자열을 두 개 알고리즘으로 해싱
    1순위. Argon2 알고리즘으로 해싱
    2순위. Bcrypt 알고리즘으로 해싱
    """
    password_hash = PasswordHash((Argon2Hasher(), BcryptHasher()))
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_hash = PasswordHash((Argon2Hasher(), BcryptHasher()))
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt