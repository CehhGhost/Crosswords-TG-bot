from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.services.api_client import api_client

router = Router()

@router.message(Command("digests"))
async def cmd_digests(message: types.Message, website_user_id: int):
    """Показывает последние дайджесты пользователя"""
    
    digests = await api_client.get_user_digests(message.from_user.id)
    
    if not digests or not digests.get("digests"):
        await message.answer("📭 У вас пока нет дайджестов.")
        return
    
    keyboard = []
    for digest in digests["digests"][:5]:
        digest_id = digest["id"]
        title = digest["title"]
        date = digest["date"]
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"📰 {title} ({date})",
                callback_data=f"digest_{digest_id}"
            )
        ])
    
    await message.answer(
        "📚 Ваши последние дайджесты:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@router.callback_query(lambda c: c.data.startswith("digest_"))
async def show_digest(callback: types.CallbackQuery):
    """Показывает конкретный дайджест"""
    digest_id = callback.data.split("_")[1]
    
    digest = await api_client.get_digest(callback.from_user.id, digest_id)
    
    if not digest:
        await callback.answer("❌ Дайджест не найден", show_alert=True)
        return
    
    text = digest.get("text", "")
    if len(text) > 1000:
        text = text[:997] + "..."
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Читать полностью", url=f"https://crosswords-corpus.press/digests/{digest_id}")],
        [InlineKeyboardButton(text="🔙 Назад к списку", callback_data="back_to_digests")]
    ])
    
    await callback.message.edit_text(
        f"📰 **{digest.get('title')}**\n\n{text}",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.message(Command("subscribe"))
async def cmd_subscribe(message: types.Message):
    """Управление подписками на уведомления"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Включить уведомления", callback_data="notifications_on")],
        [InlineKeyboardButton(text="❌ Отключить уведомления", callback_data="notifications_off")],
        [InlineKeyboardButton(text="📋 Мои подписки", callback_data="my_subscriptions")]
    ])
    
    await message.answer(
        "⚙️ Настройки уведомлений Telegram\n\n"
        "Здесь вы можете управлять получением дайджестов в Telegram.",
        reply_markup=keyboard
    )

@router.callback_query(lambda c: c.data == "notifications_on")
async def enable_notifications(callback: types.CallbackQuery):
    """Включает уведомления"""
    success = await api_client.update_telegram_settings(
        callback.from_user.id,
        mobile_notifications=True
    )
    
    if success:
        await callback.message.edit_text("✅ Уведомления Telegram включены!")
    else:
        await callback.message.edit_text("❌ Не удалось обновить настройки")
    await callback.answer()

@router.callback_query(lambda c: c.data == "notifications_off")
async def disable_notifications(callback: types.CallbackQuery):
    """Отключает уведомления"""
    success = await api_client.update_telegram_settings(
        callback.from_user.id,
        mobile_notifications=False
    )
    
    if success:
        await callback.message.edit_text("🔕 Уведомления Telegram отключены")
    else:
        await callback.message.edit_text("❌ Не удалось обновить настройки")
    await callback.answer()