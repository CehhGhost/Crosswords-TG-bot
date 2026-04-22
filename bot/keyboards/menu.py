from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard():
    kb = [
        [KeyboardButton(text="👤 Мой профиль")],
        [KeyboardButton(text="📊 Мои заказы"), KeyboardButton(text="⚙️ Настройки")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)