from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard():
    """Главное меню для привязанных пользователей"""
    kb = [
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="📰 Дайджесты")],
        [KeyboardButton(text="🔔 Подписки"), KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def unlinked_keyboard():
    """Клавиатура для непривязанных пользователей"""
    kb = [
        [KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)