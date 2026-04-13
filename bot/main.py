import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import settings
from handlers import start
from middlewares.logging import LoggingMiddleware


logging.basicConfig(level=logging.DEBUG if settings.DEBUG else logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> web.Application | None:
	bot = Bot(
		token=settings.BOT_TOKEN,
		default=DefaultBotProperties(parse_mode=ParseMode.HTML),
	)
	dp = Dispatcher()

	dp.message.middleware(LoggingMiddleware())
	dp.include_router(start.router)

	if settings.USE_WEBHOOK:
		app = web.Application()

		async def on_shutdown(_: web.Application) -> None:
			await bot.session.close()

		await bot.set_webhook(settings.WEBHOOK_URL + settings.WEBHOOK_PATH)

		webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
		webhook_handler.register(app, path=settings.WEBHOOK_PATH)
		setup_application(app, dp, bot=bot)
		app.on_shutdown.append(on_shutdown)

		logger.info("Webhook mode enabled at path %s", settings.WEBHOOK_PATH)
		return app

	await bot.delete_webhook(drop_pending_updates=True)
	logger.info("Polling mode enabled")
	try:
		await dp.start_polling(bot)
	finally:
		await bot.session.close()

	return None


if __name__ == "__main__":
	if settings.USE_WEBHOOK:
		webhook_app = asyncio.run(main())
		web.run_app(webhook_app, host="0.0.0.0", port=8080)
	else:
		asyncio.run(main())
