from fastapi import HTTPException, status

class DuplicateUsernameError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="중복된 계정 ID입니다."
        )

class DuplicateEmailError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="중보된 E-mail 주소입니다."
        )


class UserNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자가 없습니다.",
        )


class PasswordMismatchError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="틀린 비밀번호입니다."
        )


        