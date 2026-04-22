from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

Base = declarative_base()

class UserLink(Base):
    __tablename__ = "user_links"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    website_user_id = Column(Integer, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<UserLink(telegram_id={self.telegram_id}, website_user_id={self.website_user_id})>"

# Движок и фабрика сессий
engine = create_async_engine("sqlite+aiosqlite:///./bot_db.sqlite")
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)