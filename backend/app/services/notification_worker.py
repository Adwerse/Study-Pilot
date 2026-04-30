import asyncio
import logging

from app.config import settings
from app.database import AsyncSessionLocal
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_service import NotificationService


logger = logging.getLogger(__name__)


async def notification_worker_loop() -> None:
    interval = max(1, settings.NOTIFICATIONS_POLL_INTERVAL_SECONDS)
    logger.info("Notification worker started with %s second interval", interval)

    while True:
        try:
            async with AsyncSessionLocal() as db:
                service = NotificationService(NotificationRepository(db))
                result = await service.process_due_notifications()
                if result.processed:
                    logger.info(
                        "Processed notifications processed=%s sent=%s failed=%s "
                        "cancelled=%s",
                        result.processed,
                        result.sent,
                        result.failed,
                        result.cancelled,
                    )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Notification worker iteration failed")

        await asyncio.sleep(interval)
