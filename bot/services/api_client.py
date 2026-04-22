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

    async def link_telegram(self, telegram_id: int, user_id: int, link_token: str) -> Optional[Dict[str, Any]]:
        """
        POST /users/telegram/link
        Headers: Authorization: Bearer {BACKEND_SECRET_KEY}
        Body: { "telegramId": 12345, "userId": 100, "linkToken": "uuid" }
        
        Response format (TelegramLinkResponseDTO):
        {
            "success": true,
            "userId": 100,
            "userName": "Иван",
            "error": null
        }
        """
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
                        data = await resp.json()
                        logger.info(f"Successfully linked Telegram {telegram_id} to user {user_id}")
                        return data
                    else:
                        error_text = await resp.text()
                        logger.error(f"Backend API Error {resp.status}: {error_text}")
                        
                        # Пытаемся распарсить JSON с ошибкой
                        try:
                            error_data = await resp.json()
                            return error_data
                        except:
                            return {"success": False, "error": f"HTTP {resp.status}: {error_text}"}
                            
            except aiohttp.ClientError as e:
                logger.exception(f"Connection error to backend: {e}")
                return {"success": False, "error": "Backend service unavailable"}
            except Exception as e:
                logger.exception(f"Unexpected error: {e}")
                return {"success": False, "error": "Internal error"}

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        GET /users/telegram/{telegramId}
        Headers: Authorization: Bearer {BACKEND_SECRET_KEY}
        
        Response format:
        {
            "id": 100,
            "username": "ivan",
            "email": "ivan@example.com",
            "name": "Иван",
            "surname": "Иванов",
            "verified": true
        }
        """
        url = f"{self.base_url}/telegram/{telegram_id}"
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.debug(f"Retrieved user data for Telegram {telegram_id}")
                        return data
                    elif resp.status == 404:
                        logger.info(f"No user found for Telegram {telegram_id}")
                        return None
                    else:
                        error_text = await resp.text()
                        logger.error(f"Backend API Error {resp.status}: {error_text}")
                        return None
                        
            except aiohttp.ClientError as e:
                logger.exception(f"Connection error to backend: {e}")
                return None
            except Exception as e:
                logger.exception(f"Unexpected error: {e}")
                return None

    async def check_user_exists(self, telegram_id: int) -> bool:
        """Проверяет, привязан ли Telegram ID к какому-либо пользователю"""
        user = await self.get_user_by_telegram_id(telegram_id)
        return user is not None
    
    async def get_user_digests(self, telegram_id: int) -> Optional[Dict]:
        """Получить дайджесты пользователя"""
        url = f"{self.base_url}/telegram/digests"
        params = {"telegramId": telegram_id}
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    return None
            except Exception as e:
                logger.error(f"Failed to get digests: {e}")
                return None
    
    async def get_digest(self, telegram_id: int, digest_id: str) -> Optional[Dict]:
        """Получить конкретный дайджест"""
        url = f"{self.base_url}/telegram/digest/{digest_id}"
        params = {"telegramId": telegram_id}
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    return None
            except Exception as e:
                logger.error(f"Failed to get digest: {e}")
                return None
            
    async def update_telegram_settings(self, telegram_id: int, mobile_notifications: bool) -> bool:
        """Обновить настройки уведомлений Telegram"""
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
                logger.error(f"Failed to update settings: {e}")
                return False

api_client = MainApiClient()