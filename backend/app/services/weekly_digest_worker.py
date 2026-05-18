import asyncio
import logging

from app.config import settings
from app.database import AsyncSessionLocal
from app.services.weekly_digest_service import build_weekly_digest_service


logger = logging.getLogger(__name__)


async def weekly_digest_worker_loop() -> None:
    interval = max(60, settings.WEEKLY_DIGEST_POLL_INTERVAL_SECONDS)
    logger.info("Weekly digest worker started with %s second interval", interval)

    while True:
        try:
            async with AsyncSessionLocal() as db:
                service = build_weekly_digest_service(db)
                result = await service.process_due_weekly_digests()
                if result.processed:
                    logger.info(
                        "Processed weekly digests processed=%s sent=%s failed=%s skipped=%s",
                        result.processed,
                        result.sent,
                        result.failed,
                        result.skipped,
                    )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Weekly digest worker iteration failed")

        await asyncio.sleep(interval)
