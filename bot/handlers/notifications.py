from aiogram import Bot, Router


router = Router()


async def send_focus_reminder(bot: Bot, telegram_id: int, message: str) -> None:
    # Напоминание о паузе / конце Pomodoro-сессии
    await bot.send_message(telegram_id, message)


async def send_daily_digest(bot: Bot, telegram_id: int, summary: str) -> None:
    # Дневной отчёт
    await bot.send_message(telegram_id, summary)


async def send_weekly_digest(bot: Bot, telegram_id: int, summary: str) -> None:
    # Недельный дайджест каждое воскресенье
    await bot.send_message(telegram_id, summary)