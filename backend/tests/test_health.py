import pytest

from app.api import health as health_api


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "studypilot-backend"
    assert "version" in payload
    assert "environment" in payload


@pytest.mark.asyncio
async def test_readiness_returns_503_when_database_is_unavailable(client, monkeypatch):
    class BrokenConnection:
        async def __aenter__(self):
            raise OSError("database down")

        async def __aexit__(self, exc_type, exc, tb):
            return None

    class BrokenEngine:
        def connect(self):
            return BrokenConnection()

    monkeypatch.setattr(health_api, "engine", BrokenEngine())

    response = await client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert response.json()["checks"]["database"] == "not_ready"
