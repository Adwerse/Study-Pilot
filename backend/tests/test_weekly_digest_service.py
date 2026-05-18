from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest

from app.models.user import User
from app.models.weekly_digest import WeeklyDigestDelivery
from app.schemas.analytics import (
    AnalyticsDataQuality,
    AnalyticsMetrics,
    AnalyticsNarrative,
    AnalyticsPeriod,
    AnalyticsPeriodType,
)
from app.schemas.weekly_digest import DigestPeriod
from app.services.telegram_service import TelegramSendResult
from app.services.weekly_digest_service import WeeklyDigestService


UTC = timezone.utc


class FakeDigestRepository:
    def __init__(self, candidates: list[User] | None = None):
        self.candidates = candidates or []
        self.deliveries: dict[
            tuple[UUID, datetime, datetime], WeeklyDigestDelivery
        ] = {}

    async def list_due_candidates(self) -> list[User]:
        return self.candidates

    async def claim_or_create_pending_delivery(
        self,
        *,
        user_id: UUID,
        telegram_id: int,
        week_start: datetime,
        week_end: datetime,
        timezone_name: str,
        retry_failed: bool = False,
    ) -> WeeklyDigestDelivery | None:
        key = (user_id, week_start, week_end)
        delivery = self.deliveries.get(key)
        if delivery is None:
            delivery = WeeklyDigestDelivery(
                id=uuid4(),
                user_id=user_id,
                telegram_id=telegram_id,
                week_start=week_start,
                week_end=week_end,
                timezone=timezone_name,
                status="pending",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            self.deliveries[key] = delivery
        elif delivery.status == "failed" and retry_failed:
            delivery.status = "pending"
            delivery.error_message = None
        return delivery

    async def mark_sent(
        self,
        delivery: WeeklyDigestDelivery,
        *,
        message_text: str,
        telegram_message_id: int | None,
        sent_at: datetime | None = None,
    ) -> WeeklyDigestDelivery:
        delivery.status = "sent"
        delivery.message_text = message_text
        delivery.telegram_message_id = telegram_message_id
        delivery.sent_at = sent_at or datetime.now(UTC)
        delivery.error_message = None
        return delivery

    async def mark_failed(
        self,
        delivery: WeeklyDigestDelivery,
        error_message: str,
    ) -> WeeklyDigestDelivery:
        delivery.status = "failed"
        delivery.error_message = error_message[:500]
        return delivery

    async def mark_skipped(
        self,
        delivery: WeeklyDigestDelivery,
        reason: str | None = None,
    ) -> WeeklyDigestDelivery:
        delivery.status = "skipped"
        delivery.error_message = reason
        return delivery


class FakeMetricsService:
    def __init__(
        self,
        metrics_by_user: dict[UUID, AnalyticsMetrics] | None = None,
        fail_user_id: UUID | None = None,
    ):
        self.metrics_by_user = metrics_by_user or {}
        self.fail_user_id = fail_user_id
        self.calls: list[dict[str, object]] = []

    async def build_weekly_report(
        self,
        user_id: UUID,
        week_start: date | None,
        user_timezone: ZoneInfo,
    ):
        self.calls.append(
            {
                "user_id": user_id,
                "week_start": week_start,
                "timezone": user_timezone.key,
            }
        )
        if user_id == self.fail_user_id:
            raise RuntimeError("metrics unavailable")

        metrics = self.metrics_by_user.get(
            user_id,
            AnalyticsMetrics(
                total_focus_minutes=50,
                sessions_count=2,
                completion_rate=100,
                streak_days=2,
                best_focus_hours=["09:00"],
            ),
        )
        return SimpleNamespace(
            period=AnalyticsPeriod(
                type=AnalyticsPeriodType.weekly,
                start=datetime(2026, 4, 27, tzinfo=UTC),
                end=datetime(2026, 5, 4, tzinfo=UTC),
                timezone=user_timezone.key,
            ),
            metrics=metrics,
            data_quality=AnalyticsDataQuality.medium
            if metrics.sessions_count >= 5
            else AnalyticsDataQuality.low,
            daily_breakdown=[],
        )


class FakePlanRepository:
    def __init__(self, plan=None):
        self.plan = plan

    async def get_active_by_user(self, user_id: UUID):
        _ = user_id
        return self.plan


class FakeReviewRepository:
    def __init__(self, review=None):
        self.review = review

    async def get_for_user_plan_period(self, **kwargs):
        _ = kwargs
        return self.review

    async def get_by_id_for_user(self, review_id: UUID, user_id: UUID):
        _ = (review_id, user_id)
        return self.review


class FakeTelegramService:
    def __init__(
        self,
        result: TelegramSendResult | None = None,
        results_by_telegram_id: dict[int, TelegramSendResult] | None = None,
    ):
        self.result = result or TelegramSendResult(success=True, message_id=777)
        self.results_by_telegram_id = results_by_telegram_id or {}
        self.messages: list[dict[str, object]] = []

    async def send_message(
        self,
        telegram_id: int | str | None,
        text: str,
        parse_mode: str | None = None,
        reply_markup: dict | None = None,
    ) -> TelegramSendResult:
        self.messages.append(
            {
                "telegram_id": telegram_id,
                "text": text,
                "parse_mode": parse_mode,
                "reply_markup": reply_markup,
            }
        )
        return self.results_by_telegram_id.get(int(telegram_id), self.result)


class FakeAgent:
    async def generate_report(self, **kwargs):
        _ = kwargs
        return AnalyticsNarrative(
            summary="Аналитический итог недели.",
            recommendations=["Запланируй сложные темы утром."],
        )


def make_user(
    *,
    telegram_id: int | None = 123,
    timezone_name: str = "UTC",
    notifications_enabled: bool = True,
    weekly_digest_enabled: bool = True,
) -> User:
    return User(
        id=uuid4(),
        telegram_id=telegram_id,
        timezone=timezone_name,
        notifications_enabled=notifications_enabled,
        weekly_digest_enabled=weekly_digest_enabled,
        created_at=datetime(2026, 4, 1, tzinfo=UTC),
        updated_at=datetime(2026, 4, 1, tzinfo=UTC),
    )


def make_period(user: User) -> DigestPeriod:
    return WeeklyDigestService(
        db=SimpleNamespace(commit=AsyncMock()),
        repo=FakeDigestRepository(),
        metrics_service=FakeMetricsService(),
        plan_repo=FakePlanRepository(),
        review_repo=FakeReviewRepository(),
        telegram_service=FakeTelegramService(),
        agent=FakeAgent(),
        enabled=True,
    ).get_digest_period_for_user(user, datetime(2026, 5, 3, 18, tzinfo=UTC))


def make_service(
    *,
    repo: FakeDigestRepository | None = None,
    metrics_service: FakeMetricsService | None = None,
    plan_repo: FakePlanRepository | None = None,
    review_repo: FakeReviewRepository | None = None,
    telegram_service: FakeTelegramService | None = None,
    batch_limit: int = 100,
) -> WeeklyDigestService:
    return WeeklyDigestService(
        db=SimpleNamespace(commit=AsyncMock()),
        repo=repo or FakeDigestRepository(),
        metrics_service=metrics_service or FakeMetricsService(),
        plan_repo=plan_repo or FakePlanRepository(),
        review_repo=review_repo or FakeReviewRepository(),
        telegram_service=telegram_service or FakeTelegramService(),
        agent=FakeAgent(),
        enabled=True,
        batch_limit=batch_limit,
    )


def test_digest_period_uses_user_timezone_monday_boundaries() -> None:
    user = make_user(timezone_name="Europe/Dublin")
    service = make_service()

    period = service.get_digest_period_for_user(
        user,
        datetime(2026, 5, 3, 17, 30, tzinfo=UTC),
    )

    assert period.week_start == datetime(2026, 4, 26, 23, 0, tzinfo=UTC)
    assert period.week_end == datetime(2026, 5, 3, 23, 0, tzinfo=UTC)
    assert period.week_start_date == date(2026, 4, 27)
    assert period.timezone == "Europe/Dublin"


def test_digest_period_falls_back_to_utc_for_invalid_timezone() -> None:
    user = make_user(timezone_name="Not/AZone")
    period = make_service().get_digest_period_for_user(
        user,
        datetime(2026, 5, 3, 18, 0, tzinfo=UTC),
    )

    assert period.timezone == "UTC"
    assert period.week_start == datetime(2026, 4, 27, 0, 0, tzinfo=UTC)


def test_due_only_on_sunday_after_digest_hour() -> None:
    user = make_user()
    service = make_service()

    assert service.is_user_due(user, datetime(2026, 5, 3, 18, 0, tzinfo=UTC))
    assert not service.is_user_due(user, datetime(2026, 5, 3, 17, 59, tzinfo=UTC))
    assert not service.is_user_due(user, datetime(2026, 5, 4, 18, 0, tzinfo=UTC))


@pytest.mark.asyncio
async def test_user_without_telegram_id_is_skipped() -> None:
    telegram = FakeTelegramService()
    service = make_service(telegram_service=telegram)
    user = make_user(telegram_id=None)

    result = await service.process_user_weekly_digest(
        user=user, period=make_period(user)
    )

    assert result.status == "skipped"
    assert telegram.messages == []


@pytest.mark.asyncio
async def test_disabled_digest_preferences_are_skipped() -> None:
    telegram = FakeTelegramService()
    service = make_service(telegram_service=telegram)
    user = make_user(notifications_enabled=False)

    result = await service.process_user_weekly_digest(
        user=user, period=make_period(user)
    )

    assert result.status == "skipped"
    assert telegram.messages == []


@pytest.mark.asyncio
async def test_completed_activity_sends_digest_and_marks_sent(monkeypatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "MINI_APP_URL", "https://app.example.com")
    user = make_user()
    repo = FakeDigestRepository()
    telegram = FakeTelegramService(TelegramSendResult(success=True, message_id=999))
    service = make_service(repo=repo, telegram_service=telegram)
    period = make_period(user)

    result = await service.process_user_weekly_digest(user=user, period=period)

    delivery = repo.deliveries[(user.id, period.week_start, period.week_end)]
    assert result.status == "sent"
    assert delivery.status == "sent"
    assert delivery.telegram_message_id == 999
    assert delivery.sent_at is not None
    assert telegram.messages[0]["telegram_id"] == user.telegram_id
    assert telegram.messages[0]["parse_mode"] is None
    assert telegram.messages[0]["reply_markup"] == {
        "inline_keyboard": [
            [
                {
                    "text": "Открыть аналитику",
                    "web_app": {"url": "https://app.example.com/analytics"},
                }
            ]
        ]
    }


@pytest.mark.asyncio
async def test_active_plan_with_zero_completed_sessions_is_marked_skipped() -> None:
    user = make_user()
    repo = FakeDigestRepository()
    telegram = FakeTelegramService()
    metrics_service = FakeMetricsService(
        {user.id: AnalyticsMetrics(total_focus_minutes=0, sessions_count=0)}
    )
    service = make_service(
        repo=repo,
        metrics_service=metrics_service,
        plan_repo=FakePlanRepository(plan=SimpleNamespace(id=uuid4())),
        telegram_service=telegram,
    )
    period = make_period(user)

    result = await service.process_user_weekly_digest(user=user, period=period)

    delivery = repo.deliveries[(user.id, period.week_start, period.week_end)]
    assert result.status == "skipped"
    assert delivery.status == "skipped"
    assert telegram.messages == []


@pytest.mark.asyncio
async def test_telegram_error_marks_delivery_failed() -> None:
    user = make_user()
    repo = FakeDigestRepository()
    telegram = FakeTelegramService(
        TelegramSendResult(success=False, error_message="Forbidden")
    )
    service = make_service(repo=repo, telegram_service=telegram)
    period = make_period(user)

    result = await service.process_user_weekly_digest(user=user, period=period)

    delivery = repo.deliveries[(user.id, period.week_start, period.week_end)]
    assert result.status == "failed"
    assert delivery.status == "failed"
    assert delivery.error_message == "Forbidden"


@pytest.mark.asyncio
async def test_sent_delivery_is_not_sent_twice() -> None:
    user = make_user()
    repo = FakeDigestRepository()
    telegram = FakeTelegramService()
    service = make_service(repo=repo, telegram_service=telegram)
    period = make_period(user)
    await repo.claim_or_create_pending_delivery(
        user_id=user.id,
        telegram_id=user.telegram_id,
        week_start=period.week_start,
        week_end=period.week_end,
        timezone_name=period.timezone,
    )
    delivery = repo.deliveries[(user.id, period.week_start, period.week_end)]
    delivery.status = "sent"

    result = await service.process_user_weekly_digest(user=user, period=period)

    assert result.status == "skipped"
    assert telegram.messages == []


@pytest.mark.asyncio
async def test_failed_delivery_is_not_retried_unless_requested() -> None:
    user = make_user()
    repo = FakeDigestRepository()
    telegram = FakeTelegramService()
    service = make_service(repo=repo, telegram_service=telegram)
    period = make_period(user)
    await repo.claim_or_create_pending_delivery(
        user_id=user.id,
        telegram_id=user.telegram_id,
        week_start=period.week_start,
        week_end=period.week_end,
        timezone_name=period.timezone,
    )
    delivery = repo.deliveries[(user.id, period.week_start, period.week_end)]
    delivery.status = "failed"

    skipped = await service.process_user_weekly_digest(user=user, period=period)
    retried = await service.process_user_weekly_digest(
        user=user,
        period=period,
        retry_failed=True,
    )

    assert skipped.status == "skipped"
    assert retried.status == "sent"
    assert len(telegram.messages) == 1


@pytest.mark.asyncio
async def test_process_due_continues_after_one_user_failure() -> None:
    failing_user = make_user(telegram_id=111)
    sent_user = make_user(telegram_id=222)
    repo = FakeDigestRepository(candidates=[failing_user, sent_user])
    metrics_service = FakeMetricsService(fail_user_id=failing_user.id)
    service = make_service(repo=repo, metrics_service=metrics_service)

    result = await service.process_due_weekly_digests(
        now=datetime(2026, 5, 3, 18, 0, tzinfo=UTC)
    )

    assert result.processed == 2
    assert result.failed == 1
    assert result.sent == 1


@pytest.mark.asyncio
async def test_weekly_review_generation_is_draft_only(monkeypatch) -> None:
    from app.services import weekly_digest_service as digest_module

    user = make_user()
    review_id = uuid4()
    generated_review = SimpleNamespace(review_id=review_id)
    stored_review = SimpleNamespace(
        id=review_id,
        summary="Итог из weekly review.",
        recommendations=["Рекомендация из weekly review."],
    )
    calls: list[dict[str, object]] = []

    class GenerateThenLoadReviewRepository(FakeReviewRepository):
        async def get_for_user_plan_period(self, **kwargs):
            _ = kwargs
            return None

        async def get_by_id_for_user(self, review_id: UUID, user_id: UUID):
            _ = (review_id, user_id)
            return stored_review

    class FakeWeeklyReviewService:
        async def generate_review(self, **kwargs):
            calls.append(kwargs)
            return generated_review

    monkeypatch.setattr(
        digest_module,
        "build_weekly_review_service",
        lambda db: FakeWeeklyReviewService(),
    )
    repo = FakeDigestRepository()
    telegram = FakeTelegramService()
    service = make_service(
        repo=repo,
        plan_repo=FakePlanRepository(plan=SimpleNamespace(id=uuid4())),
        review_repo=GenerateThenLoadReviewRepository(),
        telegram_service=telegram,
    )

    result = await service.process_user_weekly_digest(
        user=user, period=make_period(user)
    )

    assert result.status == "sent"
    assert calls[0]["apply_changes"] is False
    assert "Итог из weekly review." in str(telegram.messages[0]["text"])
