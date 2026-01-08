import pytest
from fastapi import status
from fastapi.testclient import TestClient
from appserver.apps.account.models import User

UPDTABLE_FIELDS = frozenset(["display_name", "email"])

@pytest.mark.parametrize("payload", [
    {"display_name": "푸딩캠프"},
    {"email": "hannal@example.com"},
    {"display_name": "푸딩캠프", "email": "hannal@example.com"},
])
async def test_사용자가_변경하는_항목만_변경되고_나머지는_기존_값을_유지한다(
    client_with_auth: TestClient,
    payload: dict,
    host_user: User,
):
    # 현재 사용자 정보를 보관한다.
    before_data = host_user.model_dump()

    response = client_with_auth.patch("/account/@me", json=payload)