import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, status
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from bot.config import settings
from bot.db.models import init_models, async_session
from bot.handlers import start, commands, digests
from bot.middlewares.auth import AuthMiddleware
from bot.services.api_client import api_client # Импорт чтобы проинициализировать

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Хранилище FSM в Redis
redis_client = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
storage = RedisStorage(redis=redis_client)

# Инициализация Aiogram
bot = Bot(
    token=settings.BOT_TOKEN.get_secret_value(),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=storage)

# Регистрируем Middleware и Роутеры
dp.message.middleware(AuthMiddleware())
dp.include_router(start.router)
dp.include_router(commands.router)
dp.include_router(digests.router)

# --- Lifespan для FastAPI ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # При старте
    await init_models()
    await bot.set_webhook(
        url=f"{settings.BOT_WEBHOOK_URL}/webhook",
        secret_token=settings.BOT_WEBHOOK_SECRET.get_secret_value()
    )
    logging.info(f"Webhook set to {settings.BOT_WEBHOOK_URL}/webhook")
    yield
    # При завершении
    await bot.session.close()
    await redis_client.close()

app = FastAPI(lifespan=lifespan)

# --- Эндпоинт для получения обновлений от Telegram ---
@app.post("/webhook")
async def telegram_webhook(request: Request):
    # Проверяем секретный заголовок
    secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret_token != settings.BOT_WEBHOOK_SECRET.get_secret_value():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid secret")
    
    json_data = await request.json()
    update = Update.model_validate(json_data)
    
    # Передаем сессию БД в хендлеры через контекст
    async with async_session() as session:
        await dp.feed_update(bot, update, session=session)
    
    return {"status": "ok"}

# Для удобства локальной отладки можно добавить эндпоинт healthcheck
@app.get("/health")
async def health():
    return {"status": "running"}

# Добавить новый эндпоинт
@app.post("/internal/send-digest")
async def send_digest_notification(request: Request):
    """Принимает дайджест от Java-бэкенда и отправляет пользователю"""
    
    # Проверяем внутренний секрет
    secret = request.headers.get("X-Internal-Secret")
    if secret != settings.TELEGRAM_BOT_INTERNAL_SECRET.get_secret_value():
        raise HTTPException(status_code=401, detail="Invalid secret")
    
    data = await request.json()
    telegram_id = data.get("telegramId")
    digest_id = data.get("digestId")
    title = data.get("title")
    text = data.get("text")
    
    # Формируем сообщение
    message_text = (
        f"📰 **{title}**\n\n"
        f"{text}\n\n"
        f"🔗 [Открыть полную версию](https://crosswords-corpus.press/digests/{digest_id})"
    )
    
    # Создаем клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Читать полностью", url=f"https://crosswords-corpus.press/digests/{digest_id}")],
        [
            InlineKeyboardButton(text="⭐ Оценить", callback_data=f"rate_{digest_id}"),
            InlineKeyboardButton(text="🔔 Настройки", callback_data="settings")
        ]
    ])
    
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=message_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
        return {"status": "sent"}
    except Exception as e:
        logger.error(f"Failed to send digest to {telegram_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)