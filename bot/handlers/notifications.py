from aiogram import Bot, Router


router = Router()


async def send_focus_reminder(bot: Bot, telegram_id: int, message: str) -> None:
    # Reminder about a break or the end of a Pomodoro session
    await bot.send_message(telegram_id, message)


async def send_daily_digest(bot: Bot, telegram_id: int, summary: str) -> None:
    # Daily summary
    await bot.send_message(telegram_id, summary)


async def send_weekly_digest(bot: Bot, telegram_id: int, summary: str) -> None:
    # Weekly digest sent every Sunday
    await bot.send_message(telegram_id, summary)
