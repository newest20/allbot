import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка токена из переменных окружения
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

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
        # Получаем список участников чата
        members = await context.bot.get_chat_members(update.message.chat.id)
        
        # Формируем список упоминаний
        mentions = []
        for member in members:
            user = member.user
            if not user.is_bot:  # Пропускаем ботов
                if user.username:
                    mentions.append(f"@{user.username}")
                else:
                    # Экранируем специальные символы для MarkdownV2
                    name = user.full_name.replace('_', '\\_').replace('*', '\\*')
                    mentions.append(f"[{name}](tg://user?id={user.id})")
        
        if not mentions:
            await update.message.reply_text("В чате нет участников для упоминания!")
            return

        # Отправляем сообщение с упоминаниями
        message = ", ".join(mentions)
        await update.message.reply_text(
            message,
            parse_mode='MarkdownV2',
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Ошибка при получении списка участников: {e}")
        await update.message.reply_text(
            "Произошла ошибка при получении списка участников. "
            "Убедитесь, что у бота есть права на чтение списка участников."
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