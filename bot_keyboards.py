"""
Клавиатуры для навигации по боту
"""

from telegram import ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard():
    """Главная клавиатура - первый уровень"""
    keyboard = [
        [KeyboardButton("🔍 Подобрать отель")],
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


def get_cities_keyboard():
    """Клавиатура выбора города"""
    keyboard = [
        [KeyboardButton("🏛 Москва")],
        [KeyboardButton("🏰 Санкт-Петербург")],
        [KeyboardButton("🏖 Сочи")],
        [KeyboardButton("❌ Отменить")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_price_range_keyboard():
    """Клавиатура выбора ценового диапазона"""
    keyboard = [
        [KeyboardButton("💵 Эконом (до 3500 ₽)")],
        [KeyboardButton("💰 Средний (3500-8000 ₽)")],
        [KeyboardButton("💎 Премиум (8000-15000 ₽)")],
        [KeyboardButton("👑 Люкс (от 15000 ₽)")],
        [KeyboardButton("🔙 Назад"), KeyboardButton("❌ Отменить")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_hotels_keyboard(hotels_count: int):
    """Клавиатура выбора отеля из списка"""
    keyboard = []
    for i in range(1, min(hotels_count + 1, 10)):
        keyboard.append([KeyboardButton(f"{i}. Выбрать отель #{i}")])
    keyboard.append([KeyboardButton("🔙 Назад"), KeyboardButton("❌ Отменить")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_room_selection_keyboard(rooms_count: int):
    """Клавиатура выбора типа номера"""
    keyboard = []
    for i in range(1, rooms_count + 1):
        keyboard.append([KeyboardButton(f"Номер {i}")])
    keyboard.append([KeyboardButton("🔙 Назад"), KeyboardButton("❌ Отменить")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_guests_keyboard():
    """Клавиатура выбора количества гостей"""
    keyboard = [
        [KeyboardButton("1 гость"), KeyboardButton("2 гостя")],
        [KeyboardButton("3 гостя"), KeyboardButton("4 гостя")],
        [KeyboardButton("5 гостей"), KeyboardButton("6 гостей")],
        [KeyboardButton("🔙 Назад"), KeyboardButton("❌ Отменить")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_hotel_details_keyboard():
    """Клавиатура для просмотра деталей отеля"""
    keyboard = [
        [KeyboardButton("📋 Показать все номера")],
        [KeyboardButton("💰 Рассчитать стоимость")],
        [KeyboardButton("🔙 К списку отелей")],
        [KeyboardButton("❌ Отменить")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_cancel_keyboard():
    """Простая клавиатура с кнопкой отмены"""
    keyboard = [
        [KeyboardButton("❌ Отменить")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_back_to_main_keyboard():
    """Клавиатура возврата в главное меню"""
    keyboard = [
        [KeyboardButton("◀️ Назад в главное меню")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
