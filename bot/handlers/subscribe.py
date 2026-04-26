from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.services.api_client import api_client
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("subscribe"))
async def cmd_subscribe(message: types.Message, website_user_id: int):
    """Управление подписками на уведомления"""
    
    user_data = await api_client.get_user_by_telegram_id(message.from_user.id)
    
    if not user_data:
        await message.answer("❌ Не удалось получить настройки")
        return
    
    mobile_enabled = user_data.get("mobileNotifications", False)
    status = "✅ Включены" if mobile_enabled else "❌ Отключены"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔕 Отключить уведомления" if mobile_enabled else "🔔 Включить уведомления",
            callback_data="toggle_notifications"
        )],
        [InlineKeyboardButton(
            text="📋 Управление подписками на сайте",
            url="https://crosswords-corpus.press/profile/subscriptions"
        )]
    ])
    
    await message.answer(
        f"⚙️ <b>Настройки уведомлений Telegram</b>\n\n"
        f"Статус: {status}\n\n"
        f"Вы будете получать дайджесты по подпискам, для которых включены мобильные уведомления.",
        reply_markup=keyboard
    )

@router.callback_query(lambda c: c.data == "toggle_notifications")
async def toggle_notifications(callback: types.CallbackQuery):
    """Переключение уведомлений"""
    
    user_data = await api_client.get_user_by_telegram_id(callback.from_user.id)
    
    if not user_data:
        await callback.answer("❌ Ошибка получения настроек", show_alert=True)
        return
    
    current = user_data.get("mobileNotifications", False)
    success = await api_client.update_telegram_settings(
        callback.from_user.id,
        mobile_notifications=not current
    )
    
    if success:
        new_status = "отключены" if current else "включены"
        await callback.message.edit_text(
            f"✅ Уведомления Telegram {new_status}!\n\n"
            f"Используйте /subscribe для управления настройками."
        )
    else:
        await callback.answer("❌ Не удалось обновить настройки", show_alert=True)
    
    await callback.answer()