import random
import string
from typing import Self
from pydantic import AwareDatetime, EmailStr, model_validator, computed_field
from sqlmodel import SQLModel, Field
from .utils import hash_password

class SignupPayload(SQLModel):
    username: str = Field(min_length=4, max_length=40, description="사용자 계정 ID")
    email: EmailStr = Field(unique=True, max_length=128, description="사용자 이메일")
    display_name: str = Field(min_length=4, max_length=40, description="사용자 표시명")
    hashed_password: str = Field(min_length=8, max_length=128, description="사용자 비밀번호")
    password_again: str = Field(min_length=8, max_length=128, description="사용자 비밀번호 확인")

    @model_validator(mode="after")
    def verify_password(self) -> Self:
        if self.hashed_password != self.password_again:
            raise ValueError("비밀번호가 일치하지 않습니다.")
        return self

    @model_validator(mode="before")
    @classmethod
    def generate_display_name(cls, data: dict):
        if not data.get("display_name"):
            data["display_name"] = "".join(
                random.choices(
                    string.ascii_letters +string.digits, k=8
                )
            )
        return data


class UserOut(SQLModel):
    username: str
    display_name: str
    is_host: bool


class LoginPayload(SQLModel):
    username: str = Field(min_length=4, max_length=40)
    password: str = Field(min_length=8, max_length=128)


class UserDetailOut(UserOut):
    email: EmailStr
    created_at: AwareDatetime
    updated_at: AwareDatetime


class UpdateUserPayload(SQLModel):
    display_name: str | None = Field(default=None, min_length=4, max_length=40)
    email: EmailStr | None = Field(default=None, max_length=128)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    password_again: str | None = Field(default=None, min_length=8, max_length=128)

    @model_validator(mode="after")
    def check_all_fields_are_none(self) -> Self:
        if not self.model_dump(exclude_none=True):
            raise ValueError("최소 하나의 필드는 반드시 제공되어야 합니다.")
        return self
    
    @model_validator(mode="after")
    def verify_password(self) -> Self:
        if self.password is not None or self.password_again is not None:
            # 둘 중 하나라도 들어오면 둘 다 있어야 함
            if not self.password or not self.password_again:
                raise ValueError("비밀번호 변경 시 password와 password_again을 모두 제공해야 합니다.")

            if self.password != self.password_again:
                raise ValueError("비밀번호가 일치하지 않습니다.")

        return self

    @computed_field
    @property
    def hashed_password(self) -> str | None:
        if self.password:
            return hash_password(self.password)
        return None