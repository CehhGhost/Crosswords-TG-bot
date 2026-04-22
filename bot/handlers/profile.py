from aiogram import Router, types
from aiogram.filters import Command

from bot.services.api_client import api_client
from bot.keyboards.menu import main_menu_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("profile"))
async def cmd_profile(message: types.Message, website_user_id: int):
    """Показывает профиль пользователя"""
    
    user_data = await api_client.get_user_by_telegram_id(message.from_user.id)
    
    if user_data:
        verified = "✅" if user_data.get("verified") else "❌"
        mobile = "✅" if user_data.get("mobileNotifications") else "❌"
        
        text = (
            f"👤 <b>Профиль пользователя</b>\n\n"
            f"🆔 ID: {user_data['id']}\n"
            f"👤 Имя: {user_data.get('name', '—')} {user_data.get('surname', '')}\n"
            f"📧 Email: {user_data.get('email', '—')}\n"
            f"🔐 Верификация: {verified}\n"
            f"📱 Уведомления Telegram: {mobile}\n"
            f"🆔 Telegram ID: {message.from_user.id}"
        )
    else:
        text = (
            f"👤 <b>Профиль пользователя</b>\n\n"
            f"🆔 ID на сайте: {website_user_id}\n"
            f"📱 Telegram ID: {message.from_user.id}"
        )
    
    await message.answer(text, reply_markup=main_menu_keyboard())