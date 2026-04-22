from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.api_client import api_client
from bot.keyboards.menu import main_menu_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("profile"))
async def cmd_profile(message: types.Message, website_user_id: int):
    """Показывает профиль пользователя"""
    
    # Получаем актуальные данные с бэкенда
    user_data = await api_client.get_user_by_telegram_id(message.from_user.id)
    
    if user_data:
        verified_status = "✅" if user_data.get("verified") else "❌"
        
        profile_text = (
            f"👤 **Профиль пользователя**\n\n"
            f"🆔 ID: {user_data['id']}\n"
            f"👤 Имя: {user_data.get('name', 'Не указано')} {user_data.get('surname', '')}\n"
            f"📧 Email: {user_data.get('email', 'Не указан')}\n"
            f"🔐 Верификация: {verified_status}\n"
            f"📱 Telegram ID: {message.from_user.id}"
        )
    else:
        profile_text = (
            f"👤 **Профиль пользователя**\n\n"
            f"🆔 Ваш ID на сайте: {website_user_id}\n"
            f"📱 Telegram ID: {message.from_user.id}"
        )
    
    await message.answer(profile_text, reply_markup=main_menu_keyboard())

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Показывает справку"""
    help_text = (
        "🤖 **Crosswords Bot - Справка**\n\n"
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/profile - Показать профиль\n"
        "/help - Показать эту справку\n\n"
        "📋 Меню:\n"
        "• Мои кроссворды - список ваших кроссвордов\n"
        "• Уведомления - настройка уведомлений\n"
        "• Поиск - поиск кроссвордов\n\n"
        "По вопросам обращайтесь в поддержку на сайте."
    )
    await message.answer(help_text)