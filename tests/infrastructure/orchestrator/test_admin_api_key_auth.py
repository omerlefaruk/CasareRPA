import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from casare_rpa.infrastructure.orchestrator.api.auth import verify_token


@pytest.mark.asyncio
async def test_verify_token_accepts_admin_api_key(monkeypatch):
    monkeypatch.setenv("ORCHESTRATOR_ADMIN_API_KEY", "supersecret")

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="supersecret")
    user = await verify_token(credentials=creds)

    assert user.is_admin is True
    assert "admin" in user.roles


@pytest.mark.asyncio
async def test_verify_token_rejects_non_matching_admin_api_key(monkeypatch):
    monkeypatch.setenv("ORCHESTRATOR_ADMIN_API_KEY", "supersecret")

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="wrong")

    with pytest.raises(HTTPException) as exc:
        await verify_token(credentials=creds)

    assert exc.value.status_code == 401
