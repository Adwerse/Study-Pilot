from datetime import datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plan import Plan, PlanStage
from app.models.weekly_review import WeeklyReview
from app.repositories.focus_repository import FocusRepository
from app.repositories.plan_repository import PlanRepository
from app.repositories.weekly_review_repository import WeeklyReviewRepository
from app.schemas.weekly_review import (
    ApplyWeeklyReviewResponse,
    ProposedChange,
    WeeklyReviewHistoryItem,
    WeeklyReviewHistoryResponse,
    WeeklyReviewMetrics,
    WeeklyReviewPeriod,
    WeeklyReviewResponse,
)
from app.services.analytics_metrics_service import AnalyticsMetricsService
from app.services.roadmap_progress_analyzer import ReviewPeriod, RoadmapProgressAnalyzer
from app.services.weekly_review_agent import WeeklyReviewAgent, weekly_review_agent


class WeeklyReviewServiceError(Exception):
    status_code = 400

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class WeeklyReviewNotFoundError(WeeklyReviewServiceError):
    status_code = 404


class WeeklyReviewConflictError(WeeklyReviewServiceError):
    status_code = 409


class WeeklyReviewValidationError(WeeklyReviewServiceError):
    status_code = 422


class WeeklyReviewService:
    def __init__(
        self,
        *,
        db: AsyncSession,
        plan_repo: PlanRepository,
        focus_repo: FocusRepository,
        review_repo: WeeklyReviewRepository,
        metrics_service: AnalyticsMetricsService,
        analyzer: RoadmapProgressAnalyzer | None = None,
        agent: WeeklyReviewAgent | None = None,
    ):
        self.db = db
        self.plan_repo = plan_repo
        self.focus_repo = focus_repo
        self.review_repo = review_repo
        self.metrics_service = metrics_service
        self.analyzer = analyzer or RoadmapProgressAnalyzer()
        self.agent = agent or weekly_review_agent

    async def generate_review(
        self,
        *,
        user_id: UUID,
        plan_id: UUID | None,
        week_start,
        user_timezone: ZoneInfo,
        apply_changes: bool,
    ) -> WeeklyReviewResponse:
        plan = await self._resolve_plan(user_id=user_id, plan_id=plan_id)
        weekly_metrics = await self.metrics_service.build_weekly_report(
            user_id=user_id,
            week_start=week_start,
            user_timezone=user_timezone,
        )
        focus_sessions = await self.focus_repo.list_sessions_between(
            user_id=user_id,
            start_utc=weekly_metrics.period.start,
            end_utc=weekly_metrics.period.end,
            statuses=("completed", "cancelled"),
        )
        period = ReviewPeriod(
            start=weekly_metrics.period.start,
            end=weekly_metrics.period.end,
            timezone=weekly_metrics.period.timezone,
        )
        stages = self._ordered_stages(plan)
        analysis = self.analyzer.analyze(
            plan=plan,
            stages=stages,
            period=period,
            focus_sessions=focus_sessions,
            weekly_metrics=weekly_metrics.metrics,
        )
        agent_result = await self.agent.generate_review(
            user_id=user_id,
            plan=plan,
            stages=stages,
            weekly_metrics=weekly_metrics,
            focus_sessions=focus_sessions,
            timezone=user_timezone,
            period=period,
            deterministic_analysis=analysis,
            daily_breakdown=weekly_metrics.daily_breakdown,
        )

        try:
            review = await self.review_repo.create(
                user_id=user_id,
                plan_id=plan.id,
                period_start=period.start,
                period_end=period.end,
                timezone_name=period.timezone,
                summary=agent_result.summary,
                insights=agent_result.insights,
                risks=agent_result.risks,
                recommendations=agent_result.recommendations,
                metrics=agent_result.metrics.model_dump(mode="json"),
                proposed_changes=[
                    change.model_dump(mode="json")
                    for change in agent_result.proposed_changes
                ],
            )
            if apply_changes:
                self._apply_reschedule_changes(review=review, plan=plan)
            await self.db.commit()
            await self.db.refresh(review)
        except Exception:
            await self.db.rollback()
            raise

        return self.build_response(review)

    async def apply_review(
        self,
        *,
        user_id: UUID,
        review_id: UUID,
    ) -> ApplyWeeklyReviewResponse:
        review = await self.review_repo.get_by_id_for_user(review_id, user_id)
        if review is None:
            raise WeeklyReviewNotFoundError("Review not found")
        if review.status != "draft":
            raise WeeklyReviewConflictError("Review is already applied")

        plan = await self.plan_repo.get_owned_by_id(review.plan_id, user_id)
        if plan is None:
            raise WeeklyReviewNotFoundError("Plan not found")

        try:
            applied_count, skipped = self._apply_reschedule_changes(
                review=review,
                plan=plan,
            )
            await self.db.commit()
            await self.db.refresh(review)
        except WeeklyReviewServiceError:
            await self.db.rollback()
            raise
        except Exception:
            await self.db.rollback()
            raise

        return ApplyWeeklyReviewResponse(
            review_id=review.id,
            status="applied",
            applied_changes_count=applied_count,
            skipped_changes=skipped or None,
        )

    async def list_history(
        self,
        *,
        user_id: UUID,
        plan_id: UUID | None,
        limit: int,
        offset: int,
    ) -> WeeklyReviewHistoryResponse:
        items, total = await self.review_repo.list_history(
            user_id=user_id,
            plan_id=plan_id,
            limit=limit,
            offset=offset,
        )
        return WeeklyReviewHistoryResponse(
            items=[
                WeeklyReviewHistoryItem(
                    review_id=item.id,
                    plan_id=item.plan_id,
                    period_start=item.period_start,
                    period_end=item.period_end,
                    status=item.status,
                    summary=item.summary,
                    created_at=item.created_at,
                )
                for item in items
            ],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def _resolve_plan(self, *, user_id: UUID, plan_id: UUID | None) -> Plan:
        if plan_id is not None:
            plan = await self.plan_repo.get_owned_by_id(plan_id, user_id)
            if plan is None:
                raise WeeklyReviewNotFoundError("Plan not found")
            return plan

        plan = await self.plan_repo.get_active_by_user(user_id)
        if plan is None:
            raise WeeklyReviewNotFoundError("Active plan not found")
        return plan

    def _apply_reschedule_changes(
        self,
        *,
        review: WeeklyReview,
        plan: Plan,
    ) -> tuple[int, list[ProposedChange]]:
        stages_by_id = {str(stage.id): stage for stage in self._ordered_stages(plan)}
        applied_count = 0
        skipped: list[ProposedChange] = []

        for raw_change in review.proposed_changes or []:
            try:
                change = ProposedChange.model_validate(raw_change)
            except Exception as exc:
                raise WeeklyReviewValidationError("Invalid proposed changes") from exc

            if change.type != "reschedule_stage":
                skipped.append(change)
                continue

            stage = stages_by_id.get(str(change.stage_id))
            if stage is None:
                raise WeeklyReviewValidationError("Invalid proposed changes")
            self._validate_reschedule_change(change=change, stage=stage)

            stage.start_date = change.new_start_date
            stage.end_date = change.new_end_date
            applied_count += 1

        now = datetime.now(timezone.utc)
        review.status = "applied"
        review.applied_at = now
        if applied_count:
            plan.adapted_at = now
        return applied_count, skipped

    @staticmethod
    def _validate_reschedule_change(
        *,
        change: ProposedChange,
        stage: PlanStage,
    ) -> None:
        if (
            change.stage_id is None
            or change.new_start_date is None
            or change.new_end_date is None
            or change.old_start_date is None
            or change.old_end_date is None
            or change.new_end_date < change.new_start_date
            or change.old_end_date < change.old_start_date
        ):
            raise WeeklyReviewValidationError("Invalid proposed changes")

        if stage.start_date is not None and stage.start_date != change.old_start_date:
            raise WeeklyReviewValidationError("Roadmap has changed since review generation")
        if stage.end_date is not None and stage.end_date != change.old_end_date:
            raise WeeklyReviewValidationError("Roadmap has changed since review generation")

    @staticmethod
    def _ordered_stages(plan: Plan) -> list[PlanStage]:
        return sorted(list(getattr(plan, "stages", []) or []), key=lambda stage: stage.order_index)

    @staticmethod
    def build_response(review: WeeklyReview) -> WeeklyReviewResponse:
        return WeeklyReviewResponse(
            review_id=review.id,
            plan_id=review.plan_id,
            period=WeeklyReviewPeriod(
                start=review.period_start,
                end=review.period_end,
                timezone=review.timezone,
            ),
            status=review.status,
            summary=review.summary,
            insights=list(review.insights or []),
            risks=list(review.risks or []),
            recommendations=list(review.recommendations or []),
            metrics=WeeklyReviewMetrics.model_validate(review.metrics or {}),
            proposed_changes=[
                ProposedChange.model_validate(change)
                for change in (review.proposed_changes or [])
            ],
        )


def build_weekly_review_service(db: AsyncSession) -> WeeklyReviewService:
    focus_repo = FocusRepository(db)
    plan_repo = PlanRepository(db)
    return WeeklyReviewService(
        db=db,
        plan_repo=plan_repo,
        focus_repo=focus_repo,
        review_repo=WeeklyReviewRepository(db),
        metrics_service=AnalyticsMetricsService(
            focus_repo=focus_repo,
            plan_repo=plan_repo,
        ),
    )


__all__ = [
    "WeeklyReviewConflictError",
    "WeeklyReviewNotFoundError",
    "WeeklyReviewService",
    "WeeklyReviewServiceError",
    "WeeklyReviewValidationError",
    "build_weekly_review_service",
]
