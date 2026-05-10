from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from app.models.plan import Plan, PlanStage
from app.models.weekly_review import WeeklyReview
from app.services.weekly_review_service import (
    WeeklyReviewConflictError,
    WeeklyReviewService,
    WeeklyReviewValidationError,
)


UTC = timezone.utc


class FakeReviewRepository:
    def __init__(self, review: WeeklyReview | None):
        self.review = review

    async def get_by_id_for_user(
        self,
        review_id: UUID,
        user_id: UUID,
    ) -> WeeklyReview | None:
        if self.review and self.review.id == review_id and self.review.user_id == user_id:
            return self.review
        return None


class FakePlanRepository:
    def __init__(self, plan: Plan):
        self.plan = plan

    async def get_owned_by_id(self, plan_id: UUID, user_id: UUID) -> Plan | None:
        if self.plan.id == plan_id and self.plan.user_id == user_id:
            return self.plan
        return None


def make_db():
    return SimpleNamespace(
        commit=AsyncMock(),
        rollback=AsyncMock(),
        refresh=AsyncMock(),
    )


def make_plan() -> tuple[Plan, PlanStage]:
    user_id = uuid4()
    plan_id = uuid4()
    stage = PlanStage(
        id=uuid4(),
        plan_id=plan_id,
        week_number=1,
        title="RAG API",
        deliverable="Working endpoint",
        status="in_progress",
        order_index=0,
        start_date=date(2026, 4, 27),
        end_date=date(2026, 5, 3),
    )
    plan = Plan(
        id=plan_id,
        user_id=user_id,
        title="RAG Plan",
        status="active",
        generated_at=datetime(2026, 4, 27, tzinfo=UTC),
    )
    plan.stages = [stage]
    return plan, stage


def make_review(
    *,
    user_id: UUID,
    plan_id: UUID,
    changes: list[dict],
    status: str = "draft",
) -> WeeklyReview:
    return WeeklyReview(
        id=uuid4(),
        user_id=user_id,
        plan_id=plan_id,
        period_start=datetime(2026, 4, 27, tzinfo=UTC),
        period_end=datetime(2026, 5, 4, tzinfo=UTC),
        timezone="UTC",
        status=status,
        summary="Summary",
        insights=[],
        risks=[],
        recommendations=[],
        metrics={},
        proposed_changes=changes,
        created_at=datetime(2026, 5, 4, tzinfo=UTC),
        updated_at=datetime(2026, 5, 4, tzinfo=UTC),
    )


def make_service(db, plan: Plan, review: WeeklyReview) -> WeeklyReviewService:
    return WeeklyReviewService(
        db=db,
        plan_repo=FakePlanRepository(plan),
        focus_repo=SimpleNamespace(),
        review_repo=FakeReviewRepository(review),
        metrics_service=SimpleNamespace(),
    )


@pytest.mark.asyncio
async def test_reschedule_stage_updates_only_users_stage() -> None:
    plan, stage = make_plan()
    review = make_review(
        user_id=plan.user_id,
        plan_id=plan.id,
        changes=[
            {
                "type": "reschedule_stage",
                "stage_id": str(stage.id),
                "reason": "Delayed",
                "old_start_date": "2026-04-27",
                "old_end_date": "2026-05-03",
                "new_start_date": "2026-05-04",
                "new_end_date": "2026-05-10",
            }
        ],
    )
    db = make_db()

    response = await make_service(db, plan, review).apply_review(
        user_id=plan.user_id,
        review_id=review.id,
    )

    assert response.applied_changes_count == 1
    assert stage.start_date == date(2026, 5, 4)
    assert stage.end_date == date(2026, 5, 10)
    assert review.status == "applied"
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_invalid_stage_id_causes_rollback() -> None:
    plan, stage = make_plan()
    review = make_review(
        user_id=plan.user_id,
        plan_id=plan.id,
        changes=[
            {
                "type": "reschedule_stage",
                "stage_id": str(uuid4()),
                "reason": "Invalid",
                "old_start_date": "2026-04-27",
                "old_end_date": "2026-05-03",
                "new_start_date": "2026-05-04",
                "new_end_date": "2026-05-10",
            }
        ],
    )
    db = make_db()

    with pytest.raises(WeeklyReviewValidationError):
        await make_service(db, plan, review).apply_review(
            user_id=plan.user_id,
            review_id=review.id,
        )

    assert stage.start_date == date(2026, 4, 27)
    db.rollback.assert_awaited_once()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_split_stage_is_not_auto_applied() -> None:
    plan, stage = make_plan()
    review = make_review(
        user_id=plan.user_id,
        plan_id=plan.id,
        changes=[
            {
                "type": "split_stage",
                "stage_id": str(stage.id),
                "reason": "Too large",
                "suggested_new_titles": ["Part 1", "Part 2"],
                "note": "Suggestion only",
            }
        ],
    )
    db = make_db()

    response = await make_service(db, plan, review).apply_review(
        user_id=plan.user_id,
        review_id=review.id,
    )

    assert response.applied_changes_count == 0
    assert response.skipped_changes is not None
    assert response.skipped_changes[0].type == "split_stage"
    assert stage.start_date == date(2026, 4, 27)
    assert review.status == "applied"


@pytest.mark.asyncio
async def test_cannot_apply_same_review_twice() -> None:
    plan, stage = make_plan()
    _ = stage
    review = make_review(
        user_id=plan.user_id,
        plan_id=plan.id,
        changes=[],
        status="applied",
    )
    db = make_db()

    with pytest.raises(WeeklyReviewConflictError):
        await make_service(db, plan, review).apply_review(
            user_id=plan.user_id,
            review_id=review.id,
        )


@pytest.mark.asyncio
async def test_transaction_rollback_on_failed_apply_after_valid_change() -> None:
    plan, first_stage = make_plan()
    second_stage = PlanStage(
        id=uuid4(),
        plan_id=plan.id,
        week_number=2,
        title="Second",
        deliverable="Second deliverable",
        status="pending",
        order_index=1,
        start_date=date(2026, 5, 4),
        end_date=date(2026, 5, 10),
    )
    plan.stages.append(second_stage)
    review = make_review(
        user_id=plan.user_id,
        plan_id=plan.id,
        changes=[
            {
                "type": "reschedule_stage",
                "stage_id": str(first_stage.id),
                "reason": "Delayed",
                "old_start_date": "2026-04-27",
                "old_end_date": "2026-05-03",
                "new_start_date": "2026-05-04",
                "new_end_date": "2026-05-10",
            },
            {
                "type": "reschedule_stage",
                "stage_id": str(second_stage.id),
                "reason": "Stale",
                "old_start_date": "2026-05-05",
                "old_end_date": "2026-05-11",
                "new_start_date": "2026-05-12",
                "new_end_date": "2026-05-18",
            },
        ],
    )
    db = make_db()

    with pytest.raises(WeeklyReviewValidationError):
        await make_service(db, plan, review).apply_review(
            user_id=plan.user_id,
            review_id=review.id,
        )

    db.rollback.assert_awaited_once()
    db.commit.assert_not_awaited()
