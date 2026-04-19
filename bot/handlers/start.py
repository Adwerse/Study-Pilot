import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from config import settings
from keyboards.main import get_webapp_keyboard


logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    user = message.from_user
    telegram_id = user.id if user else None
    username = user.username if user else None

    logger.info("/start from telegram_id=%s username=%s", telegram_id, username)

    first_name = user.first_name if user else "friend"
    text = (
        f"Hi, {first_name}! 👋\n\n"
        "Learning OS is your personal learning manager.\n"
        "Tap the button to open the app."
    )

    await message.answer(text, reply_markup=get_webapp_keyboard(settings.MINI_APP_URL))
