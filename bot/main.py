"""
Main Telegram Bot for 777 Gift System
Handles jackpot detection and prize distribution
"""

import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
BOT_TOKEN = os.getenv('BOT_TOKEN')
MINI_APP_URL = os.getenv('MINI_APP_URL', 'https://example.com')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Проверяем, пришёл ли пользователь после джекпота
    if context.args and context.args[0] == 'jackpot':
        keyboard = [
            [InlineKeyboardButton("🎰 Открыть рулетку призов", web_app={'url': MINI_APP_URL})]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"🎉 Поздравляем, {user.first_name}!\n\n"
            f"Вы выбили ДЖЕКПОТ! 777 🎰\n"
            f"Крутите рулетку призов и получите гарантированный подарок!",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            f"👋 Привет, {user.first_name}!\n\n"
            f"🎰 Отправь эмодзи рулетки в чат, чтобы попытать удачу!\n"
            f"Если выпадет 777 - получишь доступ к рулетке призов! 🎁"
        )


async def handle_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик эмодзи-рулетки (dice)"""
    message = update.message
    user = update.effective_user
    
    # Проверяем, что это именно слот-машина (🎰)
    if message.dice and message.dice.emoji == "🎰":
        dice_value = message.dice.value
        
        logger.info(f"User {user.id} (@{user.username}) rolled: {dice_value}")
        
        # Проверяем на джекпот (значение 64 = 777)
        # В Telegram API: 1-6 для каждого барабана, 64 = максимум (777)
        if dice_value == 64:
            # ДЖЕКПОТ! 🎉
            keyboard = [
                [InlineKeyboardButton("🎁 Забрать приз", url=f"https://t.me/okosniso_bot?start=jackpot")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await message.reply_text(
                f"🎰🎰🎰 ДЖЕКПОТ! 777! 🎰🎰🎰\n\n"
                f"🎉 Поздравляем, {user.first_name}!\n"
                f"Вы выиграли доступ к рулетке призов!\n\n"
                f"👇 Нажмите кнопку ниже, чтобы забрать приз:",
                reply_markup=reply_markup
            )
        else:
            # Не джекпот, но даём мотивацию
            await message.reply_text(
                f"😔 Не повезло... Выпало: {dice_value}\n"
                f"Попробуй ещё раз! Нужно выбить 777! 🎰"
            )


async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик данных из Mini App"""
    data = update.message.web_app_data.data
    user = update.effective_user
    
    logger.info(f"Received data from Mini App: {data}")
    
    # Здесь будет логика обработки выигрыша
    # Пока просто подтверждаем получение
    await update.message.reply_text(
        f"✅ Данные получены!\n"
        f"Подарок зарезервирован.\n"
        f"Скоро вы получите уведомление от @Lowatje"
    )


def main():
    """Запуск бота"""
    # Создаём приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Dice.SLOT_MACHINE, handle_dice))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    
    # Запускаем бота
    logger.info("🤖 Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()