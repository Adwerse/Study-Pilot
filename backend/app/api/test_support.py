from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db


router = APIRouter(prefix="/test", tags=["test"], include_in_schema=False)

E2E_USER_ID = UUID("00000000-0000-4000-8000-000000000001")
E2E_PLAN_ID = UUID("00000000-0000-4000-8000-000000000101")
E2E_STAGE_1_ID = UUID("00000000-0000-4000-8000-000000000201")
E2E_STAGE_2_ID = UUID("00000000-0000-4000-8000-000000000202")
E2E_DOCUMENT_ID = UUID("00000000-0000-4000-8000-000000000301")
E2E_CHUNK_ID = UUID("00000000-0000-4000-8000-000000000401")
E2E_REVIEW_ID = UUID("00000000-0000-4000-8000-000000000501")


class SeedRequest(BaseModel):
    telegram_id: int = 777001
    with_plan: bool = True
    with_focus: bool = False
    with_documents: bool = False
    with_analytics: bool = False
    with_weekly_review: bool = False


def require_test_secret(
    x_test_secret: str | None = Header(default=None, alias="X-Test-Secret"),
) -> None:
    if not settings.is_test_environment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if not settings.E2E_TEST_SECRET or x_test_secret != settings.E2E_TEST_SECRET:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.post("/reset", dependencies=[Depends(require_test_secret)])
async def reset_test_data(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await db.execute(
        text(
            """
            TRUNCATE TABLE
                weekly_digest_deliveries,
                weekly_reviews,
                notification_jobs,
                document_chunks,
                documents,
                focus_log,
                plan_stages,
                plans,
                metrics,
                users
            RESTART IDENTITY CASCADE
            """
        )
    )
    await db.commit()
    return {"status": "ok"}


@router.post("/seed", dependencies=[Depends(require_test_secret)])
async def seed_test_data(
    body: SeedRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    today = datetime.now(timezone.utc).date()
    await seed_user(db, body.telegram_id)

    if (
        body.with_plan
        or body.with_focus
        or body.with_analytics
        or body.with_weekly_review
    ):
        await seed_plan(db, today)
    if body.with_focus:
        await seed_focus_session(db, today, "Completed focus block", 1500)
    if body.with_analytics:
        await seed_focus_session(db, today - timedelta(days=1), "RAG", 1800)
        await seed_focus_session(db, today - timedelta(days=2), "PostgreSQL", 1200)
    if body.with_documents:
        await seed_document(db)
    if body.with_weekly_review:
        await seed_weekly_review(db, today)

    await db.commit()
    return {
        "status": "ok",
        "user_id": str(E2E_USER_ID),
        "telegram_id": body.telegram_id,
        "plan_id": str(E2E_PLAN_ID) if body.with_plan else None,
        "document_id": str(E2E_DOCUMENT_ID) if body.with_documents else None,
        "review_id": str(E2E_REVIEW_ID) if body.with_weekly_review else None,
    }


async def seed_user(db: AsyncSession, telegram_id: int) -> None:
    await db.execute(
        text(
            """
            INSERT INTO users (id, telegram_id, username, timezone)
            VALUES (:id, :telegram_id, 'e2e_tester', 'UTC')
            ON CONFLICT (telegram_id)
            DO UPDATE SET username = EXCLUDED.username, timezone = EXCLUDED.timezone
            """
        ),
        {"id": E2E_USER_ID, "telegram_id": telegram_id},
    )


async def seed_plan(db: AsyncSession, today: date) -> None:
    await db.execute(
        text(
            """
            INSERT INTO plans (id, user_id, title, status, generated_at)
            VALUES (:id, :user_id, 'E2E Python Roadmap', 'active', now())
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {"id": E2E_PLAN_ID, "user_id": E2E_USER_ID},
    )
    stage_rows = [
        (
            E2E_STAGE_1_ID,
            1,
            "Foundations",
            "Build a small study script",
            "in_progress",
            0,
            today,
            today + timedelta(days=6),
        ),
        (
            E2E_STAGE_2_ID,
            2,
            "Practice",
            "Finish a guided project",
            "pending",
            1,
            today + timedelta(days=7),
            today + timedelta(days=13),
        ),
    ]
    for (
        stage_id,
        week_number,
        title,
        deliverable,
        stage_status,
        order_index,
        start_date,
        end_date,
    ) in stage_rows:
        await db.execute(
            text(
                """
                INSERT INTO plan_stages (
                    id, plan_id, week_number, title, deliverable, status,
                    order_index, start_date, end_date
                )
                VALUES (
                    :id, :plan_id, :week_number, :title, :deliverable, :status,
                    :order_index, :start_date, :end_date
                )
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {
                "id": stage_id,
                "plan_id": E2E_PLAN_ID,
                "week_number": week_number,
                "title": title,
                "deliverable": deliverable,
                "status": stage_status,
                "order_index": order_index,
                "start_date": start_date,
                "end_date": end_date,
            },
        )


async def seed_focus_session(
    db: AsyncSession, session_date: date, topic: str, seconds: int
) -> None:
    started_at = datetime.combine(
        session_date, datetime.min.time(), tzinfo=timezone.utc
    ).replace(hour=10)
    await db.execute(
        text(
            """
            INSERT INTO focus_log (
                user_id, plan_id, plan_stage_id, topic, status, started_at,
                ended_at, planned_duration_minutes, actual_duration_seconds,
                difficulty, notes
            )
            VALUES (
                :user_id, :plan_id, :stage_id, :topic, 'completed', :started_at,
                :ended_at, 25, :seconds, 3, 'Seeded e2e session'
            )
            """
        ),
        {
            "user_id": E2E_USER_ID,
            "plan_id": E2E_PLAN_ID,
            "stage_id": E2E_STAGE_1_ID,
            "topic": topic,
            "started_at": started_at,
            "ended_at": started_at + timedelta(seconds=seconds),
            "seconds": seconds,
        },
    )


async def seed_document(db: AsyncSession) -> None:
    await db.execute(
        text(
            """
            INSERT INTO documents (
                id, user_id, title, filename, content_type, size_bytes,
                source_type, status, chunks_count
            )
            VALUES (
                :id, :user_id, 'Focus Notes', 'focus-notes.txt', 'text/plain',
                128, 'upload', 'ready', 1
            )
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {"id": E2E_DOCUMENT_ID, "user_id": E2E_USER_ID},
    )
    await db.execute(
        text(
            """
            INSERT INTO document_chunks (
                id, document_id, user_id, chunk_index, content, token_count,
                metadata, embedding
            )
            VALUES (
                :id, :document_id, :user_id, 0, :content, 12,
                '{"source_type":"upload"}'::jsonb, CAST(:embedding AS vector)
            )
            ON CONFLICT (document_id, chunk_index) DO NOTHING
            """
        ),
        {
            "id": E2E_CHUNK_ID,
            "document_id": E2E_DOCUMENT_ID,
            "user_id": E2E_USER_ID,
            "content": "Focus loops work best when goals, sessions, notes, and review stay connected.",
            "embedding": fake_vector_literal(),
        },
    )


async def seed_weekly_review(db: AsyncSession, today: date) -> None:
    week_start = today - timedelta(days=today.weekday())
    period_start = datetime.combine(
        week_start, datetime.min.time(), tzinfo=timezone.utc
    )
    await db.execute(
        text(
            """
            INSERT INTO weekly_reviews (
                id, user_id, plan_id, period_start, period_end, timezone,
                status, roadmap_status, summary, insights, risks,
                recommendations, metrics, proposed_changes
            )
            VALUES (
                :id, :user_id, :plan_id, :period_start, :period_end, 'UTC',
                'draft', 'on_track', 'Seeded weekly review',
                '["Focus time is visible."]'::jsonb,
                '[]'::jsonb,
                '["Keep the same rhythm."]'::jsonb,
                CAST(:metrics AS jsonb),
                '[]'::jsonb
            )
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {
            "id": E2E_REVIEW_ID,
            "user_id": E2E_USER_ID,
            "plan_id": E2E_PLAN_ID,
            "period_start": period_start,
            "period_end": period_start + timedelta(days=7),
            "metrics": (
                '{"actual_focus_minutes":25,"completed_stages_count":0,'
                '"planned_stages_count":1,"total_stages_count":2,'
                '"roadmap_progress_percent":0}'
            ),
        },
    )


def fake_vector_literal() -> str:
    dimensions = max(1, settings.EMBEDDING_DIMENSIONS)
    values = ["1.0"] + ["0.0"] * (dimensions - 1)
    return "[" + ",".join(values) + "]"
