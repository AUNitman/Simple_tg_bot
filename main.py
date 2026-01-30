import logging
import re
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from bot_knowledge import get_knowledge_base
from bot_keyboards import get_main_keyboard, get_section_keyboard

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


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений с навигацией"""
    user = update.effective_user
    message_text = update.message.text
    
    # Инициализация состояния пользователя
    if 'navigation_state' not in context.user_data:
        context.user_data['navigation_state'] = 'main'
    
    logger.info(f"User {user.id} ({user.first_name}): {message_text}")
    
    # === ГЛАВНОЕ МЕНЮ ===
    if message_text == "◀️ Назад в главное меню":
        context.user_data['navigation_state'] = 'main'
        await update.message.reply_text(
            "📱 **Главное меню**\n\nВыберите раздел:",
            reply_markup=get_main_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # === РАЗДЕЛЫ ПЕРВОГО УРОВНЯ ===
    if message_text == "🏨 Бронирование отелей":
        context.user_data['navigation_state'] = 'booking'
        await update.message.reply_text(
            "🏨 **Бронирование отелей**\n\nВыберите тему:",
            reply_markup=get_section_keyboard('booking'),
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "💳 Оплата и возврат":
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
