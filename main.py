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
from bot_keyboards import get_main_keyboard, get_section_keyboard, get_subsection_keyboard

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = "5735189716:AAHPlH_BIVLn5d52l82GBPXfPIUMGMXUGno"


class B2BTariffBot:
    """Бот для ответов на вопросы по B2B-тарифам"""
    
    def __init__(self):
        self.knowledge_base = get_knowledge_base()
        
        # Синонимы для улучшения поиска
        self.synonyms = {
            "b2b": ["б2б", "бизнес", "корпоративный", "корпоратив", "b 2 b"],
            "тариф": ["тарифы", "расценки", "цены", "прайс"],
            "скидка": ["скидки", "дисконт", "процент"],
            "комиссия": ["комиссии", "процент яндекса", "сколько платить"],
            "подключить": ["подключение", "создать", "настроить", "включить", "добавить"],
            "отключить": ["выключить", "удалить", "убрать", "отключение"],
            "отель": ["отели", "гостиница", "гостиницы", "объект"],
            "апартаменты": ["апарты", "квартира", "жильё", "жилье"],
            "документы": ["документ", "закрывающие", "акты", "справка"],
            "экстранет": ["extranet", "личный кабинет", "кабинет партнёра"],
            "бронирование": ["бронь", "брони", "забронировать", "заказ"],
            "клиент": ["клиенты", "гость", "гости", "компания", "юрлицо"],
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

Я бот-помощник по **B2B-тарифам** Яндекс Путешествий для партнёров.

Используйте древовидное меню для навигации:
📚 Общая информация
⚙️ Подключение и настройка
💼 Условия и комиссии
📋 Документы и поддержка

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
        return """🤔 Не нашёл информацию по вашему вопросу в документации по B2B-тарифам.

**Попробуйте спросить:**
• Что такое B2B-тариф?
• Какая комиссия?
• Как подключить для отеля?
• Как подключить для апартаментов?
• Какие документы нужны?

Или выберите тему из меню ниже 👇

📞 По другим вопросам обратитесь в **службу поддержки** через Экстранет."""


# Создаём экземпляр бота
bot = B2BTariffBot()


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
    help_text = """📚 **Справка по боту B2B-тарифов:**

Этот бот отвечает на вопросы по документации **B2B-тарифов** Яндекс Путешествий для партнёров.

**Структура навигации:**
1️⃣ **Главное меню** — 4 основных раздела
2️⃣ **Разделы** — подразделы по темам
3️⃣ **Подразделы** — конкретные вопросы и ответы

**Как пользоваться:**
• Используйте кнопки для навигации
• Или напишите вопрос своими словами
• Кнопка "◀️ Назад" вернёт на предыдущий уровень

📞 По вопросам вне документации — служба поддержки в Экстранете."""

    await update.message.reply_text(
        help_text,
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений с древовидной навигацией"""
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
    if message_text == "📚 Общая информация":
        context.user_data['navigation_state'] = 'info'
        await update.message.reply_text(
            "📚 **Общая информация о B2B-тарифах**\n\nВыберите тему:",
            reply_markup=get_section_keyboard('info'),
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "⚙️ Подключение и настройка":
        context.user_data['navigation_state'] = 'setup'
        await update.message.reply_text(
            "⚙️ **Подключение и настройка**\n\nВыберите тип объекта или действие:",
            reply_markup=get_section_keyboard('setup'),
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "💼 Условия и комиссии":
        context.user_data['navigation_state'] = 'conditions'
        await update.message.reply_text(
            "💼 **Условия и комиссии**\n\nВыберите тему:",
            reply_markup=get_section_keyboard('conditions'),
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "📋 Документы и поддержка":
        context.user_data['navigation_state'] = 'docs'
        await update.message.reply_text(
            "📋 **Документы и поддержка**\n\nВыберите тему:",
            reply_markup=get_section_keyboard('docs'),
            parse_mode='Markdown'
        )
        return
    
    # === ПОДРАЗДЕЛЫ ВТОРОГО УРОВНЯ ===
    
    # Общая информация - подразделы
    if message_text == "📖 Основы B2B-тарифов":
        context.user_data['navigation_state'] = 'info_basics'
        await update.message.reply_text(
            "📖 **Основы B2B-тарифов**\n\nВыберите вопрос:",
            reply_markup=get_subsection_keyboard('basics'),
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "✅ Преимущества":
        context.user_data['navigation_state'] = 'info_benefits'
        await update.message.reply_text(
            "✅ **Преимущества B2B-тарифов**\n\nВыберите вопрос:",
            reply_markup=get_subsection_keyboard('benefits'),
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "👥 Участники":
        context.user_data['navigation_state'] = 'info_participants'
        await update.message.reply_text(
            "👥 **Участники B2B-тарифов**\n\nВыберите вопрос:",
            reply_markup=get_subsection_keyboard('participants'),
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "🎯 Видимость тарифа":
        context.user_data['navigation_state'] = 'info_visibility'
        await update.message.reply_text(
            "🎯 **Видимость тарифа**\n\nВыберите вопрос:",
            reply_markup=get_subsection_keyboard('visibility'),
            parse_mode='Markdown'
        )
        return
    
    # Настройка - подразделы
    elif message_text == "🏨 Отели":
        context.user_data['navigation_state'] = 'setup_hotel'
        await update.message.reply_text(
            "🏨 **Настройка для отелей**\n\nВыберите действие:",
            reply_markup=get_subsection_keyboard('hotel_setup'),
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "🏠 Апартаменты":
        context.user_data['navigation_state'] = 'setup_apartment'
        await update.message.reply_text(
            "🏠 **Настройка для апартаментов**\n\nВыберите действие:",
            reply_markup=get_subsection_keyboard('apartment_setup'),
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "🔧 Управление":
        context.user_data['navigation_state'] = 'setup_management'
        await update.message.reply_text(
            "🔧 **Управление тарифом**\n\nВыберите действие:",
            reply_markup=get_subsection_keyboard('management'),
            parse_mode='Markdown'
        )
        return
    
    # Условия - подразделы
    elif message_text == "💰 Финансовые условия":
        context.user_data['navigation_state'] = 'conditions_financial'
        await update.message.reply_text(
            "💰 **Финансовые условия**\n\nВыберите вопрос:",
            reply_markup=get_subsection_keyboard('financial'),
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "📋 Требования":
        context.user_data['navigation_state'] = 'conditions_requirements'
        await update.message.reply_text(
            "📋 **Требования**\n\nВыберите вопрос:",
            reply_markup=get_subsection_keyboard('requirements'),
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "⏱ Сроки":
        context.user_data['navigation_state'] = 'conditions_timing'
        await update.message.reply_text(
            "⏱ **Сроки**\n\nВыберите вопрос:",
            reply_markup=get_subsection_keyboard('timing'),
            parse_mode='Markdown'
        )
        return
    
    # Документы - подразделы
    elif message_text == "📄 Документооборот":
        context.user_data['navigation_state'] = 'docs_documents'
        await update.message.reply_text(
            "📄 **Документооборот**\n\nВыберите вопрос:",
            reply_markup=get_subsection_keyboard('documents'),
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "💻 Техническая поддержка":
        context.user_data['navigation_state'] = 'docs_tech'
        await update.message.reply_text(
            "💻 **Техническая поддержка**\n\nВыберите вопрос:",
            reply_markup=get_subsection_keyboard('tech_support'),
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "📊 Отчётность":
        context.user_data['navigation_state'] = 'docs_reporting'
        await update.message.reply_text(
            "📊 **Отчётность**\n\nВыберите вопрос:",
            reply_markup=get_subsection_keyboard('reporting'),
            parse_mode='Markdown'
        )
        return
    
    # === КНОПКИ ВОЗВРАТА ===
    if message_text == "◀️ Назад к общей информации":
        context.user_data['navigation_state'] = 'info'
        await update.message.reply_text(
            "📚 **Общая информация о B2B-тарифах**\n\nВыберите тему:",
            reply_markup=get_section_keyboard('info'),
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "◀️ Назад к настройке":
        context.user_data['navigation_state'] = 'setup'
        await update.message.reply_text(
            "⚙️ **Подключение и настройка**\n\nВыберите тип объекта или действие:",
            reply_markup=get_section_keyboard('setup'),
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "◀️ Назад к условиям":
        context.user_data['navigation_state'] = 'conditions'
        await update.message.reply_text(
            "💼 **Условия и комиссии**\n\nВыберите тему:",
            reply_markup=get_section_keyboard('conditions'),
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "◀️ Назад к документам":
        context.user_data['navigation_state'] = 'docs'
        await update.message.reply_text(
            "📋 **Документы и поддержка**\n\nВыберите тему:",
            reply_markup=get_section_keyboard('docs'),
            parse_mode='Markdown'
        )
        return
    
    # === КОНЕЧНЫЕ КНОПКИ С ИНФОРМАЦИЕЙ ===
    
    # Маппинг кнопок на запросы
    button_map = {
        # Общая информация
        "📖 Что такое B2B-тариф?": "что такое b2b тариф",
        "🎯 Целевая аудитория": "целевая аудитория",
        "✅ Польза для партнёров": "польза преимущества",
        "📈 Увеличение загрузки": "увеличение загрузки",
        "🏢 Кто может подключить": "кто может подключить",
        "👤 Кто может бронировать": "кто может бронировать",
        "🏷 Бейдж 'Корпоративный'": "бейдж корпоративный",
        "🔍 Фильтр поиска": "фильтр корпоративные тарифы",
        
        # Настройка
        "📝 Пошаговая инструкция для отеля": "как подключить отель",
        "📝 Пошаговая инструкция для апартаментов": "как подключить апартаменты",
        "⚠️ Важные требования": "на основе какого тариф",
        "🔄 Включение/отключение тарифа": "сколько раз включать",
        "✏️ Редактирование тарифа": "редактировать тариф",
        "⏱ Время активации изменений": "как быстро появится",
        
        # Условия
        "💵 Размер комиссии": "какая комиссия",
        "🏷 Минимальная скидка": "минимальная скидка",
        "💳 Способы оплаты": "оплата",
        "📝 Условия подключения": "условия подключения",
        "⚠️ Базовый тариф": "базовый тариф",
        "🔄 Условия отмены": "отмена бронирования",
        "⏱ Сроки активации": "как быстро появится",
        "🕐 Время обработки": "сроки",
        
        # Документы
        "📄 Документы для клиентов": "какие документы",
        "📋 Договор и акты": "документооборот",
        "💻 Работа с Экстранетом": "экстранет",
        "📞 Служба поддержки": "служба поддержки",
        "📊 Отчётность и статистика": "отчётность",
        "📈 Аналитика бронирований": "аналитика",
    }
    
    # Определяем клавиатуру для возврата в зависимости от текущего состояния
    current_state = context.user_data.get('navigation_state', 'main')
    
    if current_state == 'main':
        return_keyboard = get_main_keyboard()
    elif current_state in ['info', 'setup', 'conditions', 'docs']:
        section_map = {
            'info': 'info',
            'setup': 'setup',
            'conditions': 'conditions',
            'docs': 'docs'
        }
        return_keyboard = get_section_keyboard(section_map[current_state])
    elif current_state.startswith('info_'):
        subsection_map = {
            'info_basics': 'basics',
            'info_benefits': 'benefits',
            'info_participants': 'participants',
            'info_visibility': 'visibility'
        }
        return_keyboard = get_subsection_keyboard(subsection_map.get(current_state, 'basics'))
    elif current_state.startswith('setup_'):
        subsection_map = {
            'setup_hotel': 'hotel_setup',
            'setup_apartment': 'apartment_setup',
            'setup_management': 'management'
        }
        return_keyboard = get_subsection_keyboard(subsection_map.get(current_state, 'hotel_setup'))
    elif current_state.startswith('conditions_'):
        subsection_map = {
            'conditions_financial': 'financial',
            'conditions_requirements': 'requirements',
            'conditions_timing': 'timing'
        }
        return_keyboard = get_subsection_keyboard(subsection_map.get(current_state, 'financial'))
    elif current_state.startswith('docs_'):
        subsection_map = {
            'docs_documents': 'documents',
            'docs_tech': 'tech_support',
            'docs_reporting': 'reporting'
        }
        return_keyboard = get_subsection_keyboard(subsection_map.get(current_state, 'documents'))
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
    
    print("🤖 Бот B2B-тарифов запущен!")
    print("📱 Древовидная навигация активна")
    print("🔄 Нажмите Ctrl+C для остановки")
    application.run_polling()


if __name__ == "__main__":
    main()
