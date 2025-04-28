import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telethon.sync import TelegramClient
from telegram.helpers import escape_markdown

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка токенов из переменных окружения
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')

# Инициализация Telethon клиента
telethon_client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=TOKEN)


async def get_chat_members(chat_id):
    """Получаем список участников чата с помощью Telethon"""
    try:
        members = []
        async for user in telethon_client.iter_participants(chat_id):
            if not user.bot:  # Пропускаем ботов
                members.append({
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'username': user.username,
                    'full_name': f"{user.first_name or ''} {user.last_name or ''}".strip()
                })
        return members
    except Exception as e:
        logger.error(f"Telethon error: {e}")
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    await update.message.reply_text(
        "Привет! Я бот для тега всех участников чата. "
        "Используйте команду /all или напишите @all для упоминания всех участников."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = (
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n"
        "/all - Упомянуть всех участников чата\n\n"
        "Также можно использовать @all в любом сообщении."
    )
    await update.message.reply_text(help_text)


async def mention_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /all и @all"""
    if update.message.chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("Эта команда работает только в групповых чатах!")
        return

    try:
        # Получаем список участников чата через Telethon
        members = await get_chat_members(update.message.chat.id)

        if members is None:
            await update.message.reply_text(
                "Произошла ошибка при получении списка участников. "
                "Попробуйте позже."
            )
            return

        if not members:
            await update.message.reply_text("В чате нет участников для упоминания!")
            return

        # Формируем список упоминаний
        mentions = []
        for member in members:
            if member.get('username'):
                mentions.append(f"@{member['username']}")
            else:
                # Экранируем все специальные символы для MarkdownV2
                name = escape_markdown(member['full_name'], version=2)
                mentions.append(f"[{name}](tg://user?id={member['id']})")

        # Отправляем сообщение с упоминаниями
        message = ", ".join(mentions)
        await update.message.reply_text(
            message,
            parse_mode=None,
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Ошибка при упоминании участников: {e}")
        await update.message.reply_text(
            "Произошла ошибка при упоминании участников. "
            "Попробуйте позже."
        )


def main() -> None:
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("all", mention_all))
    application.add_handler(MessageHandler(filters.Regex(r'@all'), mention_all))

    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()