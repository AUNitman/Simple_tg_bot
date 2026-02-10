import logging
import re
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from bot_knowledge import get_knowledge_base
from bot_keyboards import (
    get_main_keyboard,
    get_section_keyboard,
    get_cities_keyboard,
    get_price_range_keyboard,
    get_hotels_keyboard,
    get_room_selection_keyboard,
    get_guests_keyboard,
    get_cancel_keyboard,
    get_back_to_main_keyboard
)
from hotel_booking import HotelBookingSystem, BookingState, init_booking_data

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = "5735189716:AAHPlH_BIVLn5d52l82GBPXfPIUMGMXUGno"


class YandexTravelBot:
    """Бот для ответов на вопросы по Яндекс Путешествиям"""
    
    def __init__(self):
        self.knowledge_base = get_knowledge_base()
        self.booking_system = HotelBookingSystem()
        
        # Синонимы для улучшения поиска
        self.synonyms = {
            "бронирование": ["бронь", "забронировать", "заказ", "резерв"],
            "отель": ["отели", "гостиница", "гостиницы", "номер"],
            "оплата": ["оплатить", "платить", "заплатить", "деньги"],
            "предоплата": ["аванс", "частичная оплата"],
            "сплит": ["split", "частями", "рассрочка"],
            "отмена": ["отменить", "отказ", "возврат"],
            "подтверждение": ["ваучер", "документ", "подтвердить"],
            "поддержка": ["помощь", "техподдержка", "служба"],
            "приложение": ["app", "мобильное"],
            "кешбэк": ["кэшбек", "бонусы", "баллы"],
        }
    
    def _get_greeting(self, user_name: str = "") -> str:
        """Динамическое приветствие"""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            time_greeting = "Доброе утро"
        elif 12 <= hour < 18:
            time_greeting = "Добрый день"
        else:
            time_greeting = "Добрый вечер"
        
        name_part = f", {user_name}" if user_name else ""
        
        return f"""👋 {time_greeting}{name_part}!

Я бот-помощник по **Яндекс Путешествиям**.

Помогу вам с:
🏨 Бронированием отелей
💳 Вопросами по оплате
ℹ️ Информацией о сервисе
📞 Технической поддержкой

**Выберите раздел** из меню ниже 👇"""
    
    def _normalize_text(self, text: str) -> str:
        """Нормализация текста"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _expand_with_synonyms(self, text: str) -> str:
        """Расширение текста синонимами"""
        expanded = text
        for main_word, syns in self.synonyms.items():
            for syn in syns:
                if syn in text:
                    expanded += f" {main_word}"
                    break
        return expanded
    
    def find_response(self, message: str, user_name: str = "") -> str:
        """Поиск ответа по сообщению"""
        normalized = self._normalize_text(message)
        expanded = self._expand_with_synonyms(normalized)
        
        best_match = None
        best_score = 0
        
        for item in self.knowledge_base:
            score = 0
            for pattern in item["patterns"]:
                pattern_lower = pattern.lower()
                if pattern_lower in expanded:
                    score += len(pattern_lower)
                    if pattern_lower in normalized:
                        score += 15  # Бонус за точное совпадение
            
            if score > best_score:
                best_score = score
                best_match = item
        
        # Если нашли совпадение
        if best_match and best_score > 0:
            if best_match["category"] == "greeting":
                return self._get_greeting(user_name)
            return best_match["response"]
        
        # Если не нашли
        return self._unknown_response()
    
    def _unknown_response(self) -> str:
        """Ответ на неизвестный вопрос"""
        return """🤔 Не нашёл информацию по вашему вопросу.

**Попробуйте спросить:**
• Как забронировать отель?
• Какие способы оплаты?
• Как отменить бронирование?
• Что такое Яндекс Путешествия?

Или выберите тему из меню ниже 👇

📞 По другим вопросам обратитесь в **службу поддержки** Яндекс Путешествий."""


# Создаём экземпляр бота
bot = YandexTravelBot()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    context.user_data['navigation_state'] = 'main'
    greeting = bot._get_greeting(user.first_name)
    
    await update.message.reply_text(
        greeting,
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """📚 **Справка по боту Яндекс Путешествий:**

Этот бот отвечает на вопросы по сервису **Яндекс Путешествия**.

**Основные разделы:**
🏨 **Бронирование отелей** — как забронировать, поиск, условия
💳 **Оплата и возврат** — способы оплаты, отмена, возврат средств
ℹ️ **О сервисе** — информация о Яндекс Путешествиях
📞 **Помощь и поддержка** — техподдержка и частые вопросы

**Как пользоваться:**
• Используйте кнопки для навигации
• Или напишите вопрос своими словами
• Кнопка "◀️ Назад" вернёт в главное меню

📞 По вопросам вне бота — служба поддержки Яндекс Путешествий."""

    await update.message.reply_text(
        help_text,
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )


async def handle_booking_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка многошагового сценария бронирования"""
    user = update.effective_user
    message_text = update.message.text
    
    # Инициализация данных бронирования
    if 'booking_data' not in context.user_data:
        context.user_data['booking_data'] = init_booking_data()
    
    booking_data = context.user_data['booking_data']
    current_state = booking_data['state']
    
    logger.info(f"Booking flow - User {user.id}, State: {current_state}, Message: {message_text}")
    
    # Обработка отмены на любом этапе
    if message_text in ["❌ Отменить бронирование", "❌ Отменить"]:
        context.user_data['booking_data'] = init_booking_data()
        context.user_data['navigation_state'] = 'main'
        await update.message.reply_text(
            "❌ Подбор отменен.\n\nВы вернулись в главное меню.",
            reply_markup=get_main_keyboard(),
            parse_mode='Markdown'
        )
        return True
    
    # === ШАГ 1: ВЫБОР ГОРОДА ===
    if current_state == BookingState.SELECTING_CITY:
        city_map = {
            "🏛 Москва": "moscow",
            "🏰 Санкт-Петербург": "saint_petersburg",
            "🏖 Сочи": "sochi"
        }
        
        if message_text in city_map:
            city_id = city_map[message_text]
            booking_data['city_id'] = city_id
            booking_data['city_name'] = message_text.split()[1]
            booking_data['state'] = BookingState.SELECTING_PRICE_RANGE
            
            await update.message.reply_text(
                f"✅ Выбран город: **{booking_data['city_name']}**\n\n"
                "💰 Теперь выберите ценовой диапазон:",
                reply_markup=get_price_range_keyboard(),
                parse_mode='Markdown'
            )
            return True
    
    # === ШАГ 2: ВЫБОР ЦЕНОВОГО ДИАПАЗОНА ===
    elif current_state == BookingState.SELECTING_PRICE_RANGE:
        if message_text == "🔙 Назад":
            booking_data['state'] = BookingState.SELECTING_CITY
            await update.message.reply_text(
                "🏙 Выберите город:",
                reply_markup=get_cities_keyboard(),
                parse_mode='Markdown'
            )
            return True
        
        price_map = {
            "💵 Эконом (до 3500 ₽)": "budget",
            "💰 Средний (3500-8000 ₽)": "medium",
            "💎 Премиум (8000-15000 ₽)": "premium",
            "👑 Люкс (от 15000 ₽)": "luxury"
        }
        
        if message_text in price_map:
            price_range = price_map[message_text]
            booking_data['price_range'] = price_range
            
            # Получаем отели
            hotels = bot.booking_system.get_hotels_by_city(booking_data['city_id'])
            filtered_hotels = bot.booking_system.filter_hotels_by_price(hotels, price_range)
            
            if not filtered_hotels:
                await update.message.reply_text(
                    "😔 К сожалению, в выбранном ценовом диапазоне отели не найдены.\n\n"
                    "Попробуйте выбрать другой диапазон:",
                    reply_markup=get_price_range_keyboard(),
                    parse_mode='Markdown'
                )
                return True
            
            booking_data['hotels'] = filtered_hotels
            booking_data['state'] = BookingState.VIEWING_HOTELS
            
            hotels_list = bot.booking_system.format_hotels_list(filtered_hotels)
            await update.message.reply_text(
                hotels_list + "\n📌 Выберите отель из списка:",
                reply_markup=get_hotels_keyboard(len(filtered_hotels)),
                parse_mode='Markdown'
            )
            return True
    
    # === ШАГ 3: ВЫБОР ОТЕЛЯ ===
    elif current_state == BookingState.VIEWING_HOTELS:
        if message_text == "🔙 Назад":
            booking_data['state'] = BookingState.SELECTING_PRICE_RANGE
            await update.message.reply_text(
                "💰 Выберите ценовой диапазон:",
                reply_markup=get_price_range_keyboard(),
                parse_mode='Markdown'
            )
            return True
        
        # Проверяем выбор отеля
        if message_text.startswith("1.") or message_text.startswith("2.") or message_text.startswith("3."):
            try:
                hotel_index = int(message_text.split(".")[0]) - 1
                if 0 <= hotel_index < len(booking_data['hotels']):
                    selected_hotel = booking_data['hotels'][hotel_index]
                    booking_data['selected_hotel_id'] = selected_hotel['id']
                    booking_data['selected_hotel_name'] = selected_hotel['name']
                    booking_data['state'] = BookingState.SELECTING_ROOM
                    
                    hotel_info = bot.booking_system.format_hotel_info(selected_hotel, show_rooms=True)
                    await update.message.reply_text(
                        hotel_info + "\n\n🏠 Выберите тип номера:",
                        reply_markup=get_room_selection_keyboard(len(selected_hotel['room_types'])),
                        parse_mode='Markdown'
                    )
                    return True
            except (ValueError, IndexError):
                pass
    
    # === ШАГ 4: ВЫБОР ТИПА НОМЕРА ===
    elif current_state == BookingState.SELECTING_ROOM:
        if message_text == "🔙 Назад":
            booking_data['state'] = BookingState.VIEWING_HOTELS
            hotels_list = bot.booking_system.format_hotels_list(booking_data['hotels'])
            await update.message.reply_text(
                hotels_list + "\n📌 Выберите отель из списка:",
                reply_markup=get_hotels_keyboard(len(booking_data['hotels'])),
                parse_mode='Markdown'
            )
            return True
        
        if message_text.startswith("Номер "):
            try:
                room_index = int(message_text.split()[1]) - 1
                hotel = bot.booking_system.get_hotel_by_id(booking_data['selected_hotel_id'])
                if hotel and 0 <= room_index < len(hotel['room_types']):
                    room = hotel['room_types'][room_index]
                    booking_data['selected_room_type'] = room['type']
                    booking_data['price_per_night'] = room['price']
                    booking_data['state'] = BookingState.COMPLETED
                    
                    # Формируем информацию о заселении и бронировании
                    info_message = f"""✅ **Выбран номер: {room['type']}**
💰 **Цена:** {room['price']:,} ₽/ночь
👥 **Вместимость:** до {room['capacity']} чел.

🏨 **Информация о заселении:**

⏰ **Время заезда и выезда:**
   • Check-in: обычно с 14:00
   • Check-out: обычно до 12:00
   • Ранний заезд/поздний выезд - по запросу

📋 **Условия бронирования:**
   • Бронирование через сайт Яндекс Путешествий
   • Или звонок напрямую в отель
   • Предоплата или полная оплата при бронировании
   {'• Бесплатная отмена до даты заезда' if hotel.get('free_cancellation') else '• Невозвратный тариф'}

🆔 **Что нужно при заселении:**
   • Паспорт или документ, удостоверяющий личность
   • Подтверждение бронирования
   • Банковская карта для депозита (если требуется)

📞 **Контакты отеля:**
   • Адрес: {hotel['address']}
   • Для бронирования: сайт Яндекс Путешествий

💡 **Дополнительная информация:**
   • Удобства: {', '.join(hotel['amenities'][:3])}
   • Рейтинг: ⭐ {hotel['rating']}/5.0

Хотите подобрать другой вариант? Нажмите "🔍 Подобрать отель" в главном меню."""
                    
                    await update.message.reply_text(
                        info_message,
                        reply_markup=get_back_to_main_keyboard(),
                        parse_mode='Markdown'
                    )
                    
                    # Сбрасываем данные
                    context.user_data['booking_data'] = init_booking_data()
                    context.user_data['navigation_state'] = 'main'
                    return True
            except (ValueError, IndexError):
                pass
    
    # === ШАГ 5: ВВОД ДАТ ===
    elif current_state == BookingState.ENTERING_DATES:
        # Проверяем формат даты
        date_pattern = r'(\d{2})\.(\d{2})\.(\d{4})'
        match = re.match(date_pattern, message_text.strip())
        
        if match:
            try:
                day, month, year = map(int, match.groups())
                check_in_date = datetime(year, month, day)
                
                # Проверяем, что дата не в прошлом
                if check_in_date.date() < datetime.now().date():
                    await update.message.reply_text(
                        "❌ Дата заезда не может быть в прошлом.\n\n"
                        "Пожалуйста, укажите корректную дату заезда:",
                        reply_markup=get_cancel_keyboard(),
                        parse_mode='Markdown'
                    )
                    return True
                
                booking_data['check_in'] = check_in_date.strftime('%d.%m.%Y')
                booking_data['state'] = BookingState.ENTERING_GUESTS
                
                await update.message.reply_text(
                    f"✅ Дата заезда: **{booking_data['check_in']}**\n\n"
                    "📅 Теперь укажите **дату выезда** в формате ДД.ММ.ГГГГ\n"
                    "Например: 18.03.2026",
                    reply_markup=get_cancel_keyboard(),
                    parse_mode='Markdown'
                )
                return True
            except ValueError:
                await update.message.reply_text(
                    "❌ Некорректная дата.\n\n"
                    "Пожалуйста, укажите дату в формате ДД.ММ.ГГГГ:",
                    reply_markup=get_cancel_keyboard(),
                    parse_mode='Markdown'
                )
                return True
    
    # === ШАГ 6: ВВОД ДАТЫ ВЫЕЗДА И КОЛИЧЕСТВА ГОСТЕЙ ===
    elif current_state == BookingState.ENTERING_GUESTS:
        # Если еще не указана дата выезда
        if not booking_data.get('check_out'):
            date_pattern = r'(\d{2})\.(\d{2})\.(\d{4})'
            match = re.match(date_pattern, message_text.strip())
            
            if match:
                try:
                    day, month, year = map(int, match.groups())
                    check_out_date = datetime(year, month, day)
                    check_in_date = datetime.strptime(booking_data['check_in'], '%d.%m.%Y')
                    
                    # Проверяем, что дата выезда после заезда
                    if check_out_date <= check_in_date:
                        await update.message.reply_text(
                            "❌ Дата выезда должна быть позже даты заезда.\n\n"
                            "Пожалуйста, укажите корректную дату выезда:",
                            reply_markup=get_cancel_keyboard(),
                            parse_mode='Markdown'
                        )
                        return True
                    
                    nights = (check_out_date - check_in_date).days
                    booking_data['check_out'] = check_out_date.strftime('%d.%m.%Y')
                    booking_data['nights'] = nights
                    
                    await update.message.reply_text(
                        f"✅ Дата выезда: **{booking_data['check_out']}**\n"
                        f"🌙 Количество ночей: **{nights}**\n\n"
                        "👥 Выберите количество гостей:",
                        reply_markup=get_guests_keyboard(),
                        parse_mode='Markdown'
                    )
                    return True
                except ValueError:
                    await update.message.reply_text(
                        "❌ Некорректная дата.\n\n"
                        "Пожалуйста, укажите дату в формате ДД.ММ.ГГГГ:",
                        reply_markup=get_cancel_keyboard(),
                        parse_mode='Markdown'
                    )
                    return True
        else:
            # Выбор количества гостей
            guests_match = re.match(r'(\d+)\s+гост', message_text)
            if guests_match:
                guests = int(guests_match.group(1))
                booking_data['guests'] = guests
                booking_data['state'] = BookingState.ENTERING_CONTACT_NAME
                
                # Рассчитываем стоимость
                calculation = bot.booking_system.calculate_total_price(
                    booking_data['selected_hotel_id'],
                    booking_data['selected_room_type'],
                    booking_data['nights'],
                    guests
                )
                
                if not calculation:
                    await update.message.reply_text(
                        "❌ Выбранный номер не подходит для указанного количества гостей.\n\n"
                        "Пожалуйста, выберите другое количество:",
                        reply_markup=get_guests_keyboard(),
                        parse_mode='Markdown'
                    )
                    return True
                
                booking_data['total'] = calculation['total']
                booking_data['free_cancellation'] = calculation['free_cancellation']
                
                booking_data['state'] = BookingState.COMPLETED
                
                # Показываем итоговую информацию
                summary = f"""✅ **Подбор завершен!**

🏨 **Отель:** {booking_data['selected_hotel_name']}
🏠 **Тип номера:** {booking_data['selected_room_type']}
👥 **Количество гостей:** {guests}

📅 **Даты:**
   • Заезд: {booking_data['check_in']}
   • Выезд: {booking_data['check_out']}
   • Ночей: {booking_data['nights']}

💰 **Стоимость:**
   • За ночь: {calculation['price_per_night']:,} ₽
   • Всего: {calculation['total']:,} ₽

{'✅ Бесплатная отмена до даты заезда' if calculation['free_cancellation'] else '❌ Невозвратный тариф'}

📞 **Для бронирования:**
Вы можете забронировать этот отель на сайте Яндекс Путешествий или позвонив в отель напрямую.

💡 Хотите подобрать другой вариант? Нажмите "🔍 Подобрать отель" в главном меню."""
                
                await update.message.reply_text(
                    summary,
                    reply_markup=get_main_keyboard(),
                    parse_mode='Markdown'
                )
                
                # Сбрасываем данные
                context.user_data['booking_data'] = init_booking_data()
                context.user_data['navigation_state'] = 'main'
                return True
    
    return False


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений с навигацией"""
    user = update.effective_user
    message_text = update.message.text
    
    # Инициализация состояния пользователя
    if 'navigation_state' not in context.user_data:
        context.user_data['navigation_state'] = 'main'
    
    logger.info(f"User {user.id} ({user.first_name}): {message_text}")
    
    # Проверяем, находимся ли мы в процессе бронирования
    if 'booking_data' in context.user_data:
        booking_data = context.user_data['booking_data']
        if booking_data['state'] != BookingState.IDLE:
            handled = await handle_booking_flow(update, context)
            if handled:
                return
    
    # === ЗАПУСК СЦЕНАРИЯ ПОДБОРА ОТЕЛЯ ===
    if message_text == "🔍 Подобрать отель":
        context.user_data['booking_data'] = init_booking_data()
        context.user_data['booking_data']['state'] = BookingState.SELECTING_CITY
        
        await update.message.reply_text(
            "🏨 **Подбор отеля**\n\n"
            "Я помогу вам найти подходящий отель и получить всю необходимую информацию.\n\n"
            "**Шаг 1:** Выберите город:",
            reply_markup=get_cities_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # === ГЛАВНОЕ МЕНЮ ===
    if message_text == "◀️ Назад в главное меню":
        context.user_data['navigation_state'] = 'main'
        context.user_data['booking_data'] = init_booking_data()
        await update.message.reply_text(
            "📱 **Главное меню**\n\nВыберите раздел:",
            reply_markup=get_main_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # === РАЗДЕЛЫ ПЕРВОГО УРОВНЯ ===
    if message_text == "💳 Оплата и возврат":
        context.user_data['navigation_state'] = 'payment'
        await update.message.reply_text(
            "💳 **Оплата и возврат**\n\nВыберите тему:",
            reply_markup=get_section_keyboard('payment'),
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "ℹ️ О сервисе":
        context.user_data['navigation_state'] = 'about'
        await update.message.reply_text(
            "ℹ️ **О сервисе Яндекс Путешествия**\n\nВыберите тему:",
            reply_markup=get_section_keyboard('about'),
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "📞 Помощь и поддержка":
        context.user_data['navigation_state'] = 'support'
        await update.message.reply_text(
            "📞 **Помощь и поддержка**\n\nВыберите тему:",
            reply_markup=get_section_keyboard('support'),
            parse_mode='Markdown'
        )
        return
    
    # === МАППИНГ КНОПОК НА ЗАПРОСЫ ===
    button_map = {
        # Бронирование отелей
        "📝 Пошаговая инструкция": "как забронировать отель",
        "🔍 Поиск и фильтры": "фильтры поиск",
        "👥 Информация о гостях": "данные гостей",
        "🏨 Условия заселения": "условия заселения",
        
        # Оплата и возврат
        "💳 Способы оплаты": "способы оплаты",
        "💰 Предоплата": "предоплата",
        "🔄 Оплата частями (Сплит)": "сплит оплата частями",
        "🔄 Отмена и возврат": "отмена бронирования",
        "📄 Подтверждение брони": "подтверждение бронирования",
        
        # О сервисе
        "✈️ О Яндекс Путешествиях": "что такое яндекс путешествия",
        "📱 Мобильное приложение": "приложение",
        "👤 Личный кабинет": "личный кабинет",
        "🎁 Бонусы и кешбэк": "бонусы кешбэк",
        "🔒 Безопасность": "безопасность",
        
        # Помощь и поддержка
        "📞 Служба поддержки": "поддержка",
        "❓ Частые вопросы": "помощь",
    }
    
    # Определяем клавиатуру для возврата в зависимости от текущего состояния
    current_state = context.user_data.get('navigation_state', 'main')
    
    if current_state == 'main':
        return_keyboard = get_main_keyboard()
    elif current_state in ['booking', 'payment', 'about', 'support']:
        return_keyboard = get_section_keyboard(current_state)
    else:
        return_keyboard = get_main_keyboard()
    
    # Обработка запроса
    query = button_map.get(message_text, message_text)
    response = bot.find_response(query, user.first_name)
    
    await update.message.reply_text(
        response,
        reply_markup=return_keyboard,
        parse_mode='Markdown'
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    if update and update.message:
        await update.message.reply_text(
            "😔 Произошла ошибка. Попробуйте ещё раз.",
            reply_markup=get_main_keyboard()
        )


def main():
    """Запуск бота"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    print("🤖 Бот Яндекс Путешествий запущен!")
    print("📱 Навигация активна")
    print("🔄 Нажмите Ctrl+C для остановки")
    application.run_polling()


if __name__ == "__main__":
    main()
