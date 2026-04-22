from aiogram import Router, types
from aiogram.filters import CommandStart, CommandObject
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.db.models import UserLink
from bot.services.api_client import api_client
from bot.keyboards.menu import main_menu_keyboard, unlinked_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(CommandStart(deep_link=True))
async def handler_start_deep_link(message: types.Message, command: CommandObject, session: AsyncSession):
    """Обработка ссылки t.me/bot?start=bind_USERID_TOKEN"""
    args = command.args
    
    if args and args.startswith("bind_"):
        await handle_binding(message, args, session)
    else:
        await handle_regular_start(message, session)

@router.message(CommandStart())
async def handler_start(message: types.Message, session: AsyncSession):
    """Обработка обычной команды /start"""
    await handle_regular_start(message, session)

async def handle_regular_start(message: types.Message, session: AsyncSession):
    """Обработка обычного запуска бота"""
    stmt = select(UserLink).where(UserLink.telegram_id == message.from_user.id)
    result = await session.execute(stmt)
    link = result.scalar_one_or_none()
    
    if link:
        await message.answer(
            f"👋 <b>С возвращением, {message.from_user.first_name}!</b>\n\n"
            "Вы привязаны к системе Crosswords.\n"
            "Используйте меню для работы с дайджестами.",
            reply_markup=main_menu_keyboard()
        )
    else:
        await message.answer(
            f"👋 <b>Добро пожаловать в Crosswords Bot, {message.from_user.first_name}!</b>\n\n"
            "Этот бот поможет вам:\n"
            "📰 Получать персонализированные дайджесты\n"
            "🔔 Настраивать уведомления\n"
            "📊 Отслеживать интересные материалы\n\n"
            "<b>🔐 Для начала работы привяжите аккаунт:</b>\n"
            "1️⃣ Войдите в личный кабинет на сайте\n"
            "2️⃣ Перейдите в Настройки → Telegram\n"
            "3️⃣ Нажмите 'Привязать Telegram'\n"
            "4️⃣ Перейдите по полученной ссылке",
            reply_markup=unlinked_keyboard()
        )

async def handle_binding(message: types.Message, args: str, session: AsyncSession):
    """Обработка привязки Telegram аккаунта"""
    processing_msg = await message.answer("🔄 Обрабатываю запрос на привязку...")
    
    try:
        params = args[5:]  # Убираем "bind_"
        parts = params.split('_', 1)
        
        if len(parts) != 2:
            await processing_msg.edit_text(
                "❌ Неверный формат ссылки привязки.\n"
                "Пожалуйста, получите новую ссылку в личном кабинете."
            )
            return
        
        user_id_str, token = parts
        
        try:
            user_id = int(user_id_str)
        except ValueError:
            await processing_msg.edit_text("❌ Некорректный идентификатор пользователя")
            return
        
        # Проверяем существующую привязку
        existing = await session.execute(
            select(UserLink).where(UserLink.telegram_id == message.from_user.id)
        )
        if existing.scalar_one_or_none():
            await processing_msg.edit_text(
                "⚠️ Ваш Telegram уже привязан к аккаунту.\n"
                "Если хотите привязать другой аккаунт, сначала отвяжите текущий в личном кабинете."
            )
            return
        
        # Отправляем запрос на бэкенд
        result = await api_client.link_telegram(
            telegram_id=message.from_user.id,
            user_id=user_id,
            link_token=token
        )
        
        if not result:
            await processing_msg.edit_text(
                "❌ Сервис временно недоступен.\nПопробуйте позже."
            )
            return
        
        if result.get("success"):
            new_link = UserLink(
                telegram_id=message.from_user.id,
                website_user_id=result["userId"]
            )
            session.add(new_link)
            await session.commit()
            
            await processing_msg.edit_text(
                f"✅ <b>Telegram успешно привязан!</b>\n\n"
                f"👤 Пользователь: {result.get('userName', 'пользователь')}\n"
                f"🆔 ID: {result['userId']}\n\n"
                f"Теперь вы можете использовать бота.",
                reply_markup=main_menu_keyboard()
            )
            logger.info(f"User {user_id} linked Telegram {message.from_user.id}")
        else:
            error = result.get("error", "Неизвестная ошибка")
            
            if "already linked" in error.lower():
                error = "Этот Telegram уже привязан к другому аккаунту."
            elif "expired" in error.lower():
                error = "Срок действия ссылки истек. Получите новую ссылку."
            elif "invalid" in error.lower():
                error = "Недействительная ссылка привязки."
            elif "not found" in error.lower():
                error = "Пользователь не найден."
            
            await processing_msg.edit_text(f"❌ Не удалось привязать аккаунт:\n{error}")
            
    except Exception as e:
        logger.exception(f"Binding error: {e}")
        await processing_msg.edit_text(
            "❌ Произошла ошибка.\nПопробуйте позже или обратитесь в поддержку."
        )