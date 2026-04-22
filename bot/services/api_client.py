import aiohttp
from bot.config import settings
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class MainApiClient:
    def __init__(self):
        self.base_url = settings.MAIN_API_BASE_URL
        self.backend_secret = settings.MAIN_API_BACKEND_SECRET.get_secret_value()
        self.headers = {
            "Authorization": f"Bearer {self.backend_secret}",
            "Content-Type": "application/json"
        }
    
    async def link_telegram(self, telegram_id: int, user_id: int, link_token: str) -> Optional[Dict]:
        """POST /users/telegram/link - Привязка Telegram к пользователю"""
        url = f"{self.base_url}/telegram/link"
        payload = {
            "telegramId": telegram_id,
            "userId": user_id,
            "linkToken": link_token
        }
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    try:
                        return await resp.json()
                    except:
                        return {"success": False, "error": await resp.text()}
            except Exception as e:
                logger.error(f"Link telegram error: {e}")
                return None
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """GET /users/telegram/{telegramId} - Получение пользователя по Telegram ID"""
        url = f"{self.base_url}/telegram/{telegram_id}"
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    return None
            except Exception as e:
                logger.error(f"Get user error: {e}")
                return None
    
    async def get_user_digests(self, telegram_id: int) -> Optional[Dict]:
        """
        Получение дайджестов пользователя через существующий эндпоинт /digests
        """
        url = f"{self.base_url.replace('/users', '')}/digests"
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(url, params={"matches_per_page": 10}) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    return None
            except Exception as e:
                logger.error(f"Get digests error: {e}")
                return None
    
    async def update_telegram_settings(self, telegram_id: int, mobile_notifications: bool) -> bool:
        """PUT /users/telegram/settings - Обновление настроек уведомлений"""
        url = f"{self.base_url}/telegram/settings"
        payload = {
            "telegramId": telegram_id,
            "mobileNotifications": mobile_notifications
        }
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.put(url, json=payload) as resp:
                    return resp.status == 200
            except Exception as e:
                logger.error(f"Update settings error: {e}")
                return False

api_client = MainApiClient()