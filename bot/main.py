import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from bot.config import settings
from bot.db.models import init_models, async_session
from bot.handlers import start, profile, digests, subscribe, help
from bot.middlewares.auth import AuthMiddleware

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Redis
redis_client = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB
)
storage = RedisStorage(redis=redis_client)

# Бот
bot = Bot(
    token=settings.BOT_TOKEN.get_secret_value(),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=storage)

# Middleware
dp.message.middleware(AuthMiddleware())
dp.callback_query.middleware(AuthMiddleware())

# Роутеры
dp.include_router(start.router)
dp.include_router(profile.router)
dp.include_router(digests.router)
dp.include_router(subscribe.router)
dp.include_router(help.router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_models()
    await bot.set_webhook(
        url=f"{settings.BOT_WEBHOOK_URL}/webhook",
        secret_token=settings.BOT_WEBHOOK_SECRET.get_secret_value()
    )
    logger.info(f"Webhook set to {settings.BOT_WEBHOOK_URL}/webhook")
    
    # Команды бота
    await bot.set_my_commands([
        types.BotCommand(command="start", description="🚀 Начать работу"),
        types.BotCommand(command="profile", description="👤 Мой профиль"),
        types.BotCommand(command="digests", description="📰 Мои дайджесты"),
        types.BotCommand(command="subscribe", description="🔔 Управление подписками"),
        types.BotCommand(command="help", description="❓ Помощь"),
    ])
    
    yield
    
    await bot.session.close()
    await redis_client.close()

app = FastAPI(lifespan=lifespan)

@app.post("/webhook")
async def telegram_webhook(request: Request):
    secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret_token != settings.BOT_WEBHOOK_SECRET.get_secret_value():
        raise HTTPException(status_code=401, detail="Invalid secret")
    
    json_data = await request.json()
    update = Update.model_validate(json_data)
    
    async with async_session() as session:
        await dp.feed_update(bot, update, session=session)
    
    return {"status": "ok"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "telegram-bot"}