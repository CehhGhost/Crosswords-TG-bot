from aiogram import Router, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.utils.deep_linking import decode_payload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.db.models import UserLink
from bot.services.api_client import api_client
from bot.keyboards.menu import main_menu_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(CommandStart(deep_link=True))
async def handler_start_deep_link(message: types.Message, command: CommandObject, session: AsyncSession):
    """Обработка ссылки вида t.me/bot?start=bind_USERID_TOKEN"""
    
    args = command.args
    if not args:
        # Обычный старт без параметров
        await handle_regular_start(message, session)
        return
    
    # Обработка deep link для привязки аккаунта
    if args.startswith("bind_"):
        await handle_binding(message, args, session)
    else:
        await message.answer(
            "👋 Добро пожаловать в Crosswords Bot!\n\n"
            "ℹ️ Чтобы привязать аккаунт:\n"
            "1️⃣ Перейдите в личный кабинет на сайте\n"
            "2️⃣ Нажмите 'Привязать Telegram'\n"
            "3️⃣ Перейдите по полученной ссылке",
            reply_markup=types.ReplyKeyboardRemove()
        )

async def handle_binding(message: types.Message, args: str, session: AsyncSession):
    """Обработка привязки Telegram аккаунта"""
    
    # Отправляем сообщение о начале обработки
    processing_msg = await message.answer("🔄 Обрабатываю запрос на привязку...")
    
    try:
        # Парсим параметры: bind_USERID_TOKEN
        # Пример: bind_123_550e8400-e29b-41d4-a716-446655440000
        params = args[5:]  # Убираем "bind_"
        parts = params.split('_', 1)  # Разделяем на userId и token (максимум 2 части)
        
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
        
        # Проверяем, не привязан ли уже этот Telegram аккаунт
        existing_link = await session.execute(
            select(UserLink).where(UserLink.telegram_id == message.from_user.id)
        )
        if existing_link.scalar_one_or_none():
            await processing_msg.edit_text(
                "⚠️ Ваш Telegram аккаунт уже привязан к пользователю сайта.\n"
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
                "❌ Сервис временно недоступен.\n"
                "Пожалуйста, попробуйте позже."
            )
            return
        
        if result.get("success"):
            # Сохраняем связку в локальной БД для быстрого доступа
            new_link = UserLink(
                telegram_id=message.from_user.id,
                website_user_id=result["userId"]
            )
            session.add(new_link)
            await session.commit()
            
            user_name = result.get("userName", "пользователь")
            await processing_msg.edit_text(
                f"✅ Telegram успешно привязан к аккаунту!\n\n"
                f"👤 Пользователь: {user_name}\n"
                f"🆔 ID: {result['userId']}\n\n"
                f"Теперь вы можете использовать бота для работы с кроссвордами.",
                reply_markup=main_menu_keyboard()
            )
            logger.info(f"User {user_id} successfully linked Telegram {message.from_user.id}")
            
        else:
            error_message = result.get("error", "Неизвестная ошибка")
            
            # Даем понятные сообщения для разных типов ошибок
            if "already linked" in error_message.lower():
                user_friendly_error = "Этот Telegram аккаунт уже привязан к другому пользователю."
            elif "expired" in error_message.lower():
                user_friendly_error = "Срок действия ссылки истек. Получите новую ссылку в личном кабинете."
            elif "invalid" in error_message.lower():
                user_friendly_error = "Недействительная ссылка привязки."
            elif "not found" in error_message.lower():
                user_friendly_error = "Пользователь не найден."
            else:
                user_friendly_error = error_message
            
            await processing_msg.edit_text(
                f"❌ Не удалось привязать аккаунт:\n"
                f"{user_friendly_error}\n\n"
                f"Пожалуйста, попробуйте получить новую ссылку в личном кабинете."
            )
            logger.warning(f"Failed to link Telegram {message.from_user.id} to user {user_id}: {error_message}")
            
    except Exception as e:
        logger.exception(f"Unexpected error during binding: {e}")
        await processing_msg.edit_text(
            "❌ Произошла непредвиденная ошибка.\n"
            "Пожалуйста, попробуйте позже или обратитесь в поддержку."
        )

async def handle_regular_start(message: types.Message, session: AsyncSession):
    """Обработка обычного запуска бота"""
    
    # Проверяем, привязан ли уже пользователь
    stmt = select(UserLink).where(UserLink.telegram_id == message.from_user.id)
    result = await session.execute(stmt)
    link = result.scalar_one_or_none()
    
    if link:
        # Пользователь уже привязан
        await message.answer(
            "👋 С возвращением!\n"
            "Вы уже привязаны к системе. Используйте меню для работы с кроссвордами.",
            reply_markup=main_menu_keyboard()
        )
    else:
        # Новый пользователь
        await message.answer(
            "👋 Добро пожаловать в Crosswords Bot!\n\n"
            "Этот бот поможет вам:\n"
            "📝 Получать уведомления о новых кроссвордах\n"
            "🔍 Искать кроссворды\n"
            "📊 Отслеживать статистику\n\n"
            "🔐 Для начала работы привяжите аккаунт:\n"
            "1️⃣ Войдите в личный кабинет на сайте\n"
            "2️⃣ Перейдите в настройки профиля\n"
            "3️⃣ Нажмите 'Привязать Telegram'\n"
            "4️⃣ Перейдите по полученной ссылке",
            reply_markup=types.ReplyKeyboardRemove()
        )