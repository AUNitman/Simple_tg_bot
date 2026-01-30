"""
Клавиатуры для навигации по боту
"""

from telegram import ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard():
    """Главная клавиатура - первый уровень"""
    keyboard = [
        [KeyboardButton("🏨 Бронирование отелей")],
        [KeyboardButton("💳 Оплата и возврат")],
        [KeyboardButton("ℹ️ О сервисе")],
        [KeyboardButton("📞 Помощь и поддержка")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_section_keyboard(section: str):
    """Клавиатура раздела - второй уровень"""
    keyboards = {
        "booking": [
            [KeyboardButton("📝 Пошаговая инструкция")],
            [KeyboardButton("🔍 Поиск и фильтры")],
            [KeyboardButton("👥 Информация о гостях")],
            [KeyboardButton("🏨 Условия заселения")],
            [KeyboardButton("◀️ Назад в главное меню")],
        ],
        "payment": [
            [KeyboardButton("💳 Способы оплаты")],
            [KeyboardButton("💰 Предоплата")],
            [KeyboardButton("🔄 Оплата частями (Сплит)")],
            [KeyboardButton("🔄 Отмена и возврат")],
            [KeyboardButton("📄 Подтверждение брони")],
            [KeyboardButton("◀️ Назад в главное меню")],
        ],
        "about": [
            [KeyboardButton("✈️ О Яндекс Путешествиях")],
            [KeyboardButton("📱 Мобильное приложение")],
            [KeyboardButton("👤 Личный кабинет")],
            [KeyboardButton("🎁 Бонусы и кешбэк")],
            [KeyboardButton("🔒 Безопасность")],
            [KeyboardButton("◀️ Назад в главное меню")],
        ],
        "support": [
            [KeyboardButton("📞 Служба поддержки")],
            [KeyboardButton("❓ Частые вопросы")],
            [KeyboardButton("◀️ Назад в главное меню")],
        ],
    }
    return ReplyKeyboardMarkup(keyboards.get(section, []), resize_keyboard=True)
