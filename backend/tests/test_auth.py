import pytest


@pytest.mark.asyncio
async def test_missing_auth_header(client):
    # GET /api/v1/users/me без заголовка -> 422 или 401
    response = await client.get("/api/v1/users/me")
    assert response.status_code in (401, 422)


@pytest.mark.asyncio
async def test_invalid_auth_prefix(client):
    # Заголовок не начинается с "tma " -> 401
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer fake_token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_init_data(client):
    # Заголовок "tma " с мусором -> 401
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": "tma garbage_data"},
    )
    assert response.status_code == 401