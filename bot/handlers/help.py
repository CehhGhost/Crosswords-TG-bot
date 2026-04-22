from aiogram import Router, types
from aiogram.filters import Command

router = Router()

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Показывает справку"""
    
    text = (
        "🤖 <b>Crosswords Bot — Справка</b>\n\n"
        "<b>📋 Доступные команды:</b>\n"
        "/start — Начать работу / привязать аккаунт\n"
        "/profile — Показать профиль\n"
        "/digests — Мои дайджесты\n"
        "/subscribe — Настройки уведомлений\n"
        "/help — Показать эту справку\n\n"
        "<b>📰 Как получать дайджесты?</b>\n"
        "1. Привяжите аккаунт через /start\n"
        "2. Включите уведомления через /subscribe\n"
        "3. Подпишитесь на интересные темы на сайте\n\n"
        "<b>🔔 Уведомления приходят автоматически</b> "
        "каждый день в 6:00 по Москве, если есть новые материалы по вашим подпискам.\n\n"
        "<b>❓ По вопросам:</b> support@crosswords-corpus.press"
    )
    
    await message.answer(text)