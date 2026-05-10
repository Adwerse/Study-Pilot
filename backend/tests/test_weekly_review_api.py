from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.api.dependencies import get_current_user
from app.database import get_db
from app.schemas.weekly_review import (
    ApplyWeeklyReviewResponse,
    WeeklyReviewHistoryResponse,
    WeeklyReviewResponse,
)
from app.services.weekly_review_service import (
    WeeklyReviewConflictError,
    WeeklyReviewNotFoundError,
)


@pytest.fixture
def weekly_review_api_overrides(app, monkeypatch):
    user_id = uuid4()
    service = None

    async def fake_current_user() -> dict:
        return {"id": 123, "username": "tester"}

    async def fake_db():
        yield object()

    async def fake_resolve_user_id(current_user, db):
        _ = (current_user, db)
        return user_id

    def fake_build_service(db):
        _ = db
        return service

    from app.api import weekly_review as weekly_review_api

    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_db] = fake_db
    monkeypatch.setattr(weekly_review_api, "resolve_user_id", fake_resolve_user_id)
    monkeypatch.setattr(
        weekly_review_api,
        "build_weekly_review_service",
        fake_build_service,
    )

    def set_service(value):
        nonlocal service
        service = value

    yield user_id, set_service
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)


def make_review_response(status: str = "draft") -> WeeklyReviewResponse:
    review_id = uuid4()
    plan_id = uuid4()
    return WeeklyReviewResponse(
        review_id=review_id,
        plan_id=plan_id,
        period={
            "start": datetime(2026, 4, 27, tzinfo=timezone.utc),
            "end": datetime(2026, 5, 4, tzinfo=timezone.utc),
            "timezone": "UTC",
        },
        status=status,
        summary="Summary",
        insights=[],
        risks=[],
        recommendations=[],
        metrics={
            "planned_focus_minutes": None,
            "actual_focus_minutes": 0,
            "completion_rate": None,
            "completed_stages_count": 0,
            "planned_stages_count": 1,
            "roadmap_progress_percent": 0,
        },
        proposed_changes=[],
    )


class FakeWeeklyReviewService:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls: list[dict] = []

    async def generate_review(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response

    async def apply_review(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return ApplyWeeklyReviewResponse(
            review_id=kwargs["review_id"],
            status="applied",
            applied_changes_count=1,
        )

    async def list_history(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return WeeklyReviewHistoryResponse(items=[], total=0, limit=10, offset=0)


@pytest.mark.asyncio
async def test_generate_weekly_review_success(client, weekly_review_api_overrides):
    _user_id, set_service = weekly_review_api_overrides
    service = FakeWeeklyReviewService(response=make_review_response())
    set_service(service)

    response = await client.post(
        "/api/v1/weekly-review/generate",
        json={"week_start": "2026-04-29", "timezone": "UTC", "apply_changes": False},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "draft"
    assert service.calls[0]["plan_id"] is None
    assert service.calls[0]["apply_changes"] is False


@pytest.mark.asyncio
async def test_generate_uses_active_plan_if_plan_id_missing(
    client,
    weekly_review_api_overrides,
):
    _user_id, set_service = weekly_review_api_overrides
    service = FakeWeeklyReviewService(response=make_review_response())
    set_service(service)

    response = await client.post("/api/v1/weekly-review/generate", json={})

    assert response.status_code == 200
    assert service.calls[0]["plan_id"] is None


@pytest.mark.asyncio
async def test_generate_rejects_foreign_plan_id(client, weekly_review_api_overrides):
    _user_id, set_service = weekly_review_api_overrides
    set_service(FakeWeeklyReviewService(error=WeeklyReviewNotFoundError("Plan not found")))

    response = await client.post(
        "/api/v1/weekly-review/generate",
        json={"plan_id": str(uuid4())},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Plan not found"


@pytest.mark.asyncio
async def test_invalid_timezone_returns_422(client, weekly_review_api_overrides):
    _user_id, set_service = weekly_review_api_overrides
    set_service(FakeWeeklyReviewService(response=make_review_response()))

    response = await client.post(
        "/api/v1/weekly-review/generate",
        json={"timezone": "Not/AZone"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid timezone"


@pytest.mark.asyncio
async def test_apply_weekly_review_endpoint_applies_draft(
    client,
    weekly_review_api_overrides,
):
    _user_id, set_service = weekly_review_api_overrides
    service = FakeWeeklyReviewService()
    set_service(service)
    review_id = uuid4()

    response = await client.post(f"/api/v1/weekly-review/{review_id}/apply")

    assert response.status_code == 200
    assert response.json()["status"] == "applied"
    assert service.calls[0]["review_id"] == review_id


@pytest.mark.asyncio
async def test_cannot_apply_same_review_twice(client, weekly_review_api_overrides):
    _user_id, set_service = weekly_review_api_overrides
    set_service(FakeWeeklyReviewService(error=WeeklyReviewConflictError("Review is already applied")))

    response = await client.post(f"/api/v1/weekly-review/{uuid4()}/apply")

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_cannot_apply_foreign_review(client, weekly_review_api_overrides):
    _user_id, set_service = weekly_review_api_overrides
    set_service(FakeWeeklyReviewService(error=WeeklyReviewNotFoundError("Review not found")))

    response = await client.post(f"/api/v1/weekly-review/{uuid4()}/apply")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_history_returns_current_users_reviews_only(
    client,
    weekly_review_api_overrides,
):
    user_id, set_service = weekly_review_api_overrides
    service = FakeWeeklyReviewService()
    set_service(service)

    response = await client.get("/api/v1/weekly-review/history")

    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert service.calls[0]["user_id"] == user_id
