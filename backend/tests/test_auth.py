import pytest

from app.config import settings


@pytest.mark.asyncio
async def test_missing_auth_header(client):
    # GET /api/v1/users/me without a header -> 422 or 401
    response = await client.get("/api/v1/users/me")
    assert response.status_code in (401, 422)


@pytest.mark.asyncio
async def test_invalid_auth_prefix(client):
    # Header does not start with "tma " -> 401
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer fake_token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_init_data(client):
    # "tma " header with garbage data -> 401
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": "tma garbage_data"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_test_auth_works_only_in_test_environment(client, monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", "test")
    monkeypatch.setattr(settings, "TESTING", True)
    monkeypatch.setattr(settings, "TEST_AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "TEST_AUTH_SECRET", "secret")

    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": "test secret:777001"},
    )

    assert response.status_code == 200
    assert response.json()["telegram_id"] == 777001


@pytest.mark.asyncio
async def test_test_auth_is_disabled_outside_test_environment(client, monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "TESTING", False)
    monkeypatch.setattr(settings, "TEST_AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "TEST_AUTH_SECRET", "secret")

    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": "test secret:777001"},
    )

    assert response.status_code == 401
