import logging
from datetime import datetime, time, timedelta, timezone
from urllib.parse import urlsplit, urlunsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.models.weekly_review import WeeklyReview
from app.repositories.focus_repository import FocusRepository
from app.repositories.plan_repository import PlanRepository
from app.repositories.weekly_digest_repository import WeeklyDigestRepository
from app.repositories.weekly_review_repository import WeeklyReviewRepository
from app.schemas.analytics import AnalyticsNarrative
from app.schemas.weekly_digest import (
    DigestPeriod,
    WeeklyDigestDeliveryResult,
    WeeklyDigestProcessResult,
    WeeklyDigestReport,
)
from app.services.analytics_agent import AnalyticsAgent, analytics_agent
from app.services.analytics_metrics_service import AnalyticsMetricsService
from app.services.telegram_service import TelegramService
from app.services.weekly_digest_formatter import WeeklyDigestFormatter
from app.services.weekly_review_service import (
    WeeklyReviewNotFoundError,
    WeeklyReviewServiceError,
    build_weekly_review_service,
)


logger = logging.getLogger(__name__)


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WeeklyDigestService:
    def __init__(
        self,
        *,
        db: AsyncSession,
        repo: WeeklyDigestRepository,
        metrics_service: AnalyticsMetricsService,
        plan_repo: PlanRepository,
        review_repo: WeeklyReviewRepository,
        telegram_service: TelegramService | None = None,
        formatter: WeeklyDigestFormatter | None = None,
        agent: AnalyticsAgent | None = None,
        enabled: bool | None = None,
        batch_limit: int | None = None,
    ):
        self.db = db
        self.repo = repo
        self.metrics_service = metrics_service
        self.plan_repo = plan_repo
        self.review_repo = review_repo
        self.telegram_service = telegram_service or TelegramService()
        self.formatter = formatter or WeeklyDigestFormatter()
        self.agent = agent or analytics_agent
        self.enabled = settings.WEEKLY_DIGEST_ENABLED if enabled is None else enabled
        self.batch_limit = (
            settings.WEEKLY_DIGEST_BATCH_LIMIT if batch_limit is None else batch_limit
        )

    async def process_due_weekly_digests(
        self,
        *,
        now: datetime | None = None,
        retry_failed: bool = False,
    ) -> WeeklyDigestProcessResult:
        if not self.enabled:
            return WeeklyDigestProcessResult()

        effective_now = ensure_utc(now or utc_now())
        logger.info("Weekly digest job started now=%s", effective_now.isoformat())
        candidates = await self.repo.list_due_candidates()
        logger.info("Weekly digest candidates=%s", len(candidates))

        processed = sent = failed = skipped = 0
        limit = max(1, int(self.batch_limit or 1))

        for user in candidates:
            if processed >= limit:
                break
            if not self.is_user_due(user, effective_now):
                continue

            result = await self.process_user_weekly_digest(
                user=user,
                now=effective_now,
                retry_failed=retry_failed,
            )
            processed += 1
            if result.status == "sent":
                sent += 1
            elif result.status == "failed":
                failed += 1
            else:
                skipped += 1

        summary = WeeklyDigestProcessResult(
            processed=processed,
            sent=sent,
            failed=failed,
            skipped=skipped,
        )
        logger.info(
            "Weekly digest job finished processed=%s sent=%s failed=%s skipped=%s",
            summary.processed,
            summary.sent,
            summary.failed,
            summary.skipped,
        )
        return summary

    async def process_user_weekly_digest(
        self,
        *,
        user: User,
        period: DigestPeriod | None = None,
        now: datetime | None = None,
        retry_failed: bool = False,
    ) -> WeeklyDigestDeliveryResult:
        effective_now = ensure_utc(now or utc_now())
        digest_period = period or self.get_digest_period_for_user(user, effective_now)

        if not self.is_user_eligible(user, digest_period):
            return WeeklyDigestDeliveryResult(
                user_id=user.id,
                status="skipped",
                error_message="User is not eligible",
            )

        try:
            return await self._process_user_weekly_digest(
                user=user,
                period=digest_period,
                retry_failed=retry_failed,
            )
        except Exception as exc:
            safe_error = self._safe_error(exc)
            logger.exception(
                "Weekly digest failed user_id=%s week_start=%s error=%s",
                user.id,
                digest_period.week_start,
                safe_error,
            )
            await self._mark_failed_if_possible(
                user=user,
                period=digest_period,
                error_message=safe_error,
                retry_failed=retry_failed,
            )
            return WeeklyDigestDeliveryResult(
                user_id=user.id,
                status="failed",
                error_message=safe_error,
            )

    def get_digest_period_for_user(self, user: User, now: datetime) -> DigestPeriod:
        user_timezone = self._resolve_timezone(getattr(user, "timezone", None))
        local_now = ensure_utc(now).astimezone(user_timezone)
        monday = local_now.date() - timedelta(days=local_now.weekday())
        start_local = datetime.combine(monday, time.min, tzinfo=user_timezone)
        end_local = start_local + timedelta(days=7)
        return DigestPeriod(
            week_start=start_local.astimezone(timezone.utc),
            week_end=end_local.astimezone(timezone.utc),
            week_start_date=monday,
            timezone=user_timezone.key,
        )

    def is_user_due(self, user: User, now: datetime) -> bool:
        user_timezone = self._resolve_timezone(getattr(user, "timezone", None))
        local_now = ensure_utc(now).astimezone(user_timezone)
        return local_now.weekday() == int(
            settings.WEEKLY_DIGEST_DAY
        ) and local_now.hour >= int(settings.WEEKLY_DIGEST_HOUR)

    def is_user_eligible(
        self,
        user: User,
        period: DigestPeriod,
        *,
        sessions_count: int | None = None,
    ) -> bool:
        _ = period
        if not getattr(user, "telegram_id", None):
            return False
        if getattr(user, "notifications_enabled", True) is False:
            return False
        if getattr(user, "weekly_digest_enabled", True) is False:
            return False
        if sessions_count is not None and sessions_count <= 0:
            return False
        return True

    async def _process_user_weekly_digest(
        self,
        *,
        user: User,
        period: DigestPeriod,
        retry_failed: bool,
    ) -> WeeklyDigestDeliveryResult:
        user_timezone = self._resolve_timezone(period.timezone)
        metrics_result = await self.metrics_service.build_weekly_report(
            user_id=user.id,
            week_start=period.week_start_date,
            user_timezone=user_timezone,
        )

        if not self.is_user_eligible(
            user,
            period,
            sessions_count=metrics_result.metrics.sessions_count,
        ):
            return await self._skip_delivery(
                user=user,
                period=period,
                reason="No completed focus sessions for digest week",
                retry_failed=retry_failed,
            )

        narrative = await self.agent.generate_report(
            period=metrics_result.period,
            metrics=metrics_result.metrics,
            daily_breakdown=metrics_result.daily_breakdown,
            data_quality=metrics_result.data_quality,
        )
        weekly_review = await self._get_or_generate_weekly_review(
            user=user,
            period=period,
            user_timezone=user_timezone,
        )
        summary, recommendations = self._choose_narrative(narrative, weekly_review)
        report = WeeklyDigestReport(
            period=period,
            metrics=metrics_result.metrics,
            data_quality=metrics_result.data_quality,
            summary=summary,
            recommendations=recommendations,
        )
        reply_markup = self._build_reply_markup()
        message_text = self.formatter.format(
            report,
            include_analytics_link=reply_markup is not None,
        )
        delivery = await self._claim_delivery(
            user=user,
            period=period,
            retry_failed=retry_failed,
        )
        if delivery is None:
            await self.db.commit()
            return WeeklyDigestDeliveryResult(
                user_id=user.id,
                status="skipped",
                error_message="Delivery is locked",
            )
        if delivery.status == "sent":
            await self.db.commit()
            return WeeklyDigestDeliveryResult(
                user_id=user.id,
                status="skipped",
                error_message="Weekly digest already sent",
            )
        if delivery.status == "skipped":
            await self.db.commit()
            return WeeklyDigestDeliveryResult(
                user_id=user.id,
                status="skipped",
                error_message="Weekly digest already skipped",
            )
        if delivery.status == "failed" and not retry_failed:
            await self.db.commit()
            return WeeklyDigestDeliveryResult(
                user_id=user.id,
                status="skipped",
                error_message="Weekly digest failed previously",
            )

        try:
            send_result = await self.telegram_service.send_message(
                telegram_id=delivery.telegram_id,
                text=message_text,
                parse_mode=None,
                reply_markup=reply_markup,
            )
        except Exception as exc:
            send_result = None
            error_message = self._safe_error(exc)
        else:
            error_message = send_result.error_message if send_result else None

        if send_result is not None and send_result.success:
            await self.repo.mark_sent(
                delivery,
                message_text=message_text,
                telegram_message_id=send_result.message_id,
            )
            logger.info(
                "Weekly digest sent user_id=%s week_start=%s message_id=%s",
                user.id,
                period.week_start,
                send_result.message_id,
            )
            return WeeklyDigestDeliveryResult(user_id=user.id, status="sent")

        safe_error = error_message or "Telegram sendMessage failed"
        await self.repo.mark_failed(delivery, safe_error)
        logger.warning(
            "Weekly digest delivery failed user_id=%s week_start=%s error=%s",
            user.id,
            period.week_start,
            safe_error,
        )
        return WeeklyDigestDeliveryResult(
            user_id=user.id,
            status="failed",
            error_message=safe_error,
        )

    async def _skip_delivery(
        self,
        *,
        user: User,
        period: DigestPeriod,
        reason: str,
        retry_failed: bool,
    ) -> WeeklyDigestDeliveryResult:
        delivery = await self._claim_delivery(
            user=user,
            period=period,
            retry_failed=retry_failed,
        )
        if delivery is None:
            await self.db.commit()
            return WeeklyDigestDeliveryResult(
                user_id=user.id,
                status="skipped",
                error_message="Delivery is locked",
            )
        if delivery.status == "pending":
            await self.repo.mark_skipped(delivery, reason)
        else:
            await self.db.commit()
        logger.info(
            "Weekly digest skipped user_id=%s week_start=%s reason=%s",
            user.id,
            period.week_start,
            reason,
        )
        return WeeklyDigestDeliveryResult(
            user_id=user.id,
            status="skipped",
            error_message=reason,
        )

    async def _mark_failed_if_possible(
        self,
        *,
        user: User,
        period: DigestPeriod,
        error_message: str,
        retry_failed: bool,
    ) -> None:
        if not getattr(user, "telegram_id", None):
            return
        delivery = await self._claim_delivery(
            user=user,
            period=period,
            retry_failed=retry_failed,
        )
        if delivery is None:
            await self.db.commit()
            return
        if delivery.status in {"pending", "failed"}:
            await self.repo.mark_failed(delivery, error_message)
        else:
            await self.db.commit()

    async def _claim_delivery(
        self,
        *,
        user: User,
        period: DigestPeriod,
        retry_failed: bool,
    ):
        return await self.repo.claim_or_create_pending_delivery(
            user_id=user.id,
            telegram_id=int(user.telegram_id),
            week_start=period.week_start,
            week_end=period.week_end,
            timezone_name=period.timezone,
            retry_failed=retry_failed,
        )

    async def _get_or_generate_weekly_review(
        self,
        *,
        user: User,
        period: DigestPeriod,
        user_timezone: ZoneInfo,
    ) -> WeeklyReview | None:
        plan = await self.plan_repo.get_active_by_user(user.id)
        if plan is None:
            return None

        existing = await self.review_repo.get_for_user_plan_period(
            user_id=user.id,
            plan_id=plan.id,
            period_start=period.week_start,
            period_end=period.week_end,
        )
        if existing is not None:
            return existing

        try:
            generated = await build_weekly_review_service(self.db).generate_review(
                user_id=user.id,
                plan_id=plan.id,
                week_start=period.week_start_date,
                user_timezone=user_timezone,
                apply_changes=False,
            )
        except WeeklyReviewNotFoundError:
            return None
        except WeeklyReviewServiceError as exc:
            logger.warning(
                "Weekly review unavailable for digest user_id=%s detail=%s",
                user.id,
                exc.detail,
            )
            return None
        except Exception:
            logger.exception(
                "Weekly review generation failed for digest user_id=%s", user.id
            )
            return None

        return await self.review_repo.get_by_id_for_user(generated.review_id, user.id)

    @staticmethod
    def _choose_narrative(
        narrative: AnalyticsNarrative,
        weekly_review: WeeklyReview | None,
    ) -> tuple[str, list[str]]:
        if weekly_review is not None:
            summary = (weekly_review.summary or "").strip()
            recommendations = [
                item.strip()
                for item in list(weekly_review.recommendations or [])
                if isinstance(item, str) and item.strip()
            ]
            if summary or recommendations:
                return (
                    summary or narrative.summary,
                    recommendations or narrative.recommendations,
                )
        return narrative.summary, narrative.recommendations

    @staticmethod
    def _resolve_timezone(timezone_name: str | None) -> ZoneInfo:
        name = (timezone_name or "UTC").strip() or "UTC"
        try:
            return ZoneInfo(name)
        except ZoneInfoNotFoundError:
            return ZoneInfo("UTC")

    @staticmethod
    def _build_reply_markup() -> dict | None:
        base_url = (settings.MINI_APP_URL or "").strip().rstrip("/")
        if not base_url:
            return None
        parsed = urlsplit(base_url)
        analytics_path = f"{parsed.path.rstrip('/')}/analytics"
        analytics_url = urlunsplit(
            (
                parsed.scheme,
                parsed.netloc,
                analytics_path,
                parsed.query,
                parsed.fragment,
            )
        )
        return {
            "inline_keyboard": [
                [
                    {
                        "text": "Открыть аналитику",
                        "web_app": {"url": analytics_url},
                    }
                ]
            ]
        }

    @staticmethod
    def _safe_error(error: Exception) -> str:
        message = str(error).splitlines()[0].strip()
        return (message or error.__class__.__name__)[:500]


def build_weekly_digest_service(db: AsyncSession) -> WeeklyDigestService:
    focus_repo = FocusRepository(db)
    plan_repo = PlanRepository(db)
    return WeeklyDigestService(
        db=db,
        repo=WeeklyDigestRepository(db),
        plan_repo=plan_repo,
        review_repo=WeeklyReviewRepository(db),
        metrics_service=AnalyticsMetricsService(
            focus_repo=focus_repo,
            plan_repo=plan_repo,
        ),
    )


__all__ = [
    "WeeklyDigestService",
    "build_weekly_digest_service",
    "ensure_utc",
    "utc_now",
]
