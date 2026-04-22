from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.db.models import UserLink
from bot.services.api_client import api_client
import logging

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseMiddleware):
    def __init__(self, check_backend: bool = True):
        """
        check_backend: проверять ли наличие пользователя на бэкенде
        """
        self.check_backend = check_backend
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Пропускаем команду /start
        if isinstance(event, Message) and event.text:
            if event.text.startswith('/start'):
                return await handler(event, data)
            
            session: AsyncSession = data['session']
            telegram_id = event.from_user.id
            
            # Проверяем локальную БД
            stmt = select(UserLink).where(UserLink.telegram_id == telegram_id)
            result = await session.execute(stmt)
            link = result.scalar_one_or_none()
            
            if not link and self.check_backend:
                # Если нет в локальной БД, проверяем на бэкенде
                logger.info(f"User {telegram_id} not found locally, checking backend")
                backend_user = await api_client.get_user_by_telegram_id(telegram_id)
                
                if backend_user:
                    # Сохраняем в локальную БД
                    new_link = UserLink(
                        telegram_id=telegram_id,
                        website_user_id=backend_user['id']
                    )
                    session.add(new_link)
                    await session.commit()
                    
                    data['website_user_id'] = backend_user['id']
                    data['user_link'] = new_link
                    logger.info(f"User {telegram_id} synced from backend")
                    return await handler(event, data)
            
            if not link:
                await event.answer(
                    "⛔ Ваш Telegram не привязан к аккаунту на сайте Crosswords.\n\n"
                    "Чтобы привязать аккаунт:\n"
                    "1️⃣ Войдите в личный кабинет на сайте\n"
                    "2️⃣ Перейдите в настройки профиля\n"
                    "3️⃣ Нажмите 'Привязать Telegram'\n"
                    "4️⃣ Перейдите по полученной ссылке",
                    reply_markup=types.ReplyKeyboardRemove()
                )
                return
            
            # Сохраняем данные в контексте
            data['website_user_id'] = link.website_user_id
            data['user_link'] = link
            
        return await handler(event, data)