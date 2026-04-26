from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware, types
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.db.models import UserLink
from bot.services.api_client import api_client
import logging

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    def __init__(self, check_backend: bool = True):
        self.check_backend = check_backend
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:

        # Определяем пользователя и объект, которому можно ответить
        if isinstance(event, Message):
            if event.text and event.text.startswith('/start'):
                return await handler(event, data)

            telegram_user = event.from_user
            answer_target = event

        elif isinstance(event, CallbackQuery):
            telegram_user = event.from_user
            answer_target = event.message

        else:
            return await handler(event, data)

        session: AsyncSession = data['session']
        telegram_id = telegram_user.id

        # Проверяем локальную БД
        stmt = select(UserLink).where(UserLink.telegram_id == telegram_id)
        result = await session.execute(stmt)
        link = result.scalar_one_or_none()

        if not link and self.check_backend:
            logger.info(f"User {telegram_id} not found locally, checking backend")
            backend_user = await api_client.get_user_by_telegram_id(telegram_id)

            if backend_user:
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
            text = (
                "⛔ Ваш Telegram не привязан к аккаунту на сайте Crosswords.\n\n"
                "Чтобы привязать аккаунт:\n"
                "1️⃣ Войдите в личный кабинет на сайте\n"
                "2️⃣ Перейдите в настройки профиля\n"
                "3️⃣ Нажмите 'Привязать Telegram'\n"
                "4️⃣ Перейдите по полученной ссылке"
            )

            if isinstance(event, CallbackQuery):
                await event.answer("⛔ Telegram не привязан к аккаунту", show_alert=True)
                if answer_target:
                    await answer_target.answer(text)
            else:
                await event.answer(text, reply_markup=types.ReplyKeyboardRemove())

            return

        data['website_user_id'] = link.website_user_id
        data['user_link'] = link

        return await handler(event, data)