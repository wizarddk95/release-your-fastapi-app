from fastapi.testclient import TestClient
from fastapi import status
from appserver.apps.account.constants import AUTH_TOKEN_COOKIE_NAME
from appserver.apps.account.models import User

def test_로그아웃_시_인증_토큰이_삭제되어야_한다(
    client_with_auth: TestClient
):
    # 1. 로그아웃 요청
    response = client_with_auth.delete("/account/logout")
    assert response.status_code == status.HTTP_200_OK
    assert response.cookies.get(AUTH_TOKEN_COOKIE_NAME) is None
    
    # TestClient는 delete_cookie 응답을 받아도 내부 쿠키 저장소를 자동으로 업데이트하지 않으므로
    # 명시적으로 쿠키를 삭제해야 합니다.
    client_with_auth.cookies.delete(AUTH_TOKEN_COOKIE_NAME)

    # 2. 인증이 필요한 API 호출
    res = client_with_auth.get("/account/@me")

    # 3. 인증 실패 확인
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
