from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.services.api_client import api_client
from bot.config import settings
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("digests"))
async def cmd_digests(message: types.Message, website_user_id: int):
    """Показывает последние дайджесты пользователя"""
    
    digests_data = await api_client.get_user_digests(message.from_user.id)
    
    if not digests_data or not digests_data.get("digests"):
        await message.answer(
            "📭 У вас пока нет доступных дайджестов.\n\n"
            "Подпишитесь на интересующие вас темы в личном кабинете на сайте!"
        )
        return
    
    digests = digests_data["digests"][:10]
    
    if not digests:
        await message.answer("📭 У вас пока нет дайджестов.")
        return
    
    # Формируем список
    text = "📰 <b>Ваши последние дайджесты:</b>\n\n"
    for i, digest in enumerate(digests, 1):
        title = digest.get("title", "Без названия")
        digest_id = digest.get("id", "")
        date = digest.get("date", "")
        if date and len(date) > 10:
            date = date[:10]
        
        text += f"{i}. <b>{title}</b>\n   📅 {date}\n"
        if digest_id:
            text += f"   🔗 /view_{digest_id}\n"
        text += "\n"
    
    text += "\n🌐 <i>Полная версия доступна на сайте</i>"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🌐 Открыть все дайджесты на сайте",
            url=f"{settings.FRONTEND_URL}/digests"
        )]
    ])
    
    await message.answer(text, reply_markup=keyboard)