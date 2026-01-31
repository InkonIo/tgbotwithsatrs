"""
Main Telegram Bot for 777 Gift System
Handles jackpot detection and prize distribution
"""

import os
import logging
import json
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import (
    get_session, User, Gift, Win, 
    init_db, add_initial_gifts
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
MINI_APP_URL = os.getenv('MINI_APP_URL', 'https://example.com')
ADMIN_ID = int(os.getenv('TEST_USER_ID', '7541069765'))
USERBOT_USERNAME = 'Lowatje'


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Сохраняем пользователя в БД
    session = get_session()
    db_user = session.query(User).filter_by(telegram_id=user.id).first()
    if not db_user:
        db_user = User(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name
        )
        session.add(db_user)
        session.commit()
        logger.info(f"New user registered: {user.id} (@{user.username})")
    session.close()
    
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
            f"Если выпадет 777 - получишь доступ к рулетке призов! 🎁\n\n"
            f"📊 Команды админа:\n"
            f"/stats - статистика\n"
            f"/add_gift - добавить подарок"
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
        if dice_value == 64:
            # ДЖЕКПОТ! 🎉
            keyboard = [
                [InlineKeyboardButton("🎁 Забрать приз", url=f"https://t.me/{context.bot.username}?start=jackpot")]
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
            # Не джекпот
            await message.reply_text(
                f"😔 Не повезло... Выпало: {dice_value}\n"
                f"Попробуй ещё раз! Нужно выбить 777! 🎰"
            )


async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик данных из Mini App"""
    data = update.message.web_app_data.data
    user = update.effective_user
    
    logger.info(f"Received data from Mini App: {data}")
    
    try:
        # Парсим данные из Mini App
        prize_data = json.loads(data)
        gift_id = prize_data.get('gift_id')
        
        if not gift_id:
            raise ValueError("gift_id not provided")
        
        session = get_session()
        
        # Получаем пользователя из БД
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        if not db_user:
            db_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name
            )
            session.add(db_user)
            session.commit()
        
        # Получаем подарок
        gift = session.query(Gift).filter_by(id=gift_id).first()
        
        if not gift:
            await update.message.reply_text("❌ Подарок не найден!")
            session.close()
            return
        
        if gift.quantity <= 0:
            await update.message.reply_text("❌ Этот подарок закончился!")
            session.close()
            return
        
        # Сохраняем выигрыш
        win = Win(
            user_id=db_user.id,
            gift_id=gift.id,
            telegram_user_id=user.id,
            status='pending'
        )
        session.add(win)
        
        # Уменьшаем количество подарков
        gift.quantity -= 1
        
        session.commit()
        
        logger.info(f"Prize saved: {gift.name} for user {user.id}. Remaining: {gift.quantity}")
        
        # Отправляем сообщение победителю
        keyboard = [
            [InlineKeyboardButton(f"💬 Написать @{USERBOT_USERNAME}", url=f"https://t.me/{USERBOT_USERNAME}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"🎉 Поздравляем!\n\n"
            f"Вы выиграли: {gift.emoji} {gift.name}!\n\n"
            f"📩 Для получения подарка:\n"
            f"1. Перейдите к @{USERBOT_USERNAME}\n"
            f"2. Отправьте ЛЮБОЙ стикер\n"
            f"3. Получите свой приз! 🎁",
            reply_markup=reply_markup
        )
        
        session.close()
        
    except Exception as e:
        logger.error(f"Error processing web app data: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке выигрыша. Попробуйте позже."
        )


async def add_gift_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /add_gift для админа"""
    user = update.effective_user
    
    # Проверяем, что это админ
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Эта команда только для админа!")
        return
    
    # Формат: /add_gift <emoji> <name> <quantity> <rarity>
    # Пример: /add_gift 💎 "Deluxe Star" 5 legendary
    
    if len(context.args) < 4:
        await update.message.reply_text(
            "📝 Использование:\n"
            "/add_gift <emoji> <name> <quantity> <rarity>\n\n"
            "Пример:\n"
            "/add_gift 💎 \"Legendary Star\" 5 legendary"
        )
        return
    
    try:
        emoji = context.args[0]
        name = ' '.join(context.args[1:-2]).strip('"')
        quantity = int(context.args[-2])
        rarity = context.args[-1]
        
        session = get_session()
        
        gift = Gift(
            emoji=emoji,
            name=name,
            quantity=quantity,
            rarity=rarity
        )
        
        session.add(gift)
        session.commit()
        
        await update.message.reply_text(
            f"✅ Подарок добавлен!\n\n"
            f"{emoji} {name}\n"
            f"Количество: {quantity}\n"
            f"Редкость: {rarity}"
        )
        
        session.close()
        
    except Exception as e:
        logger.error(f"Error adding gift: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats - статистика"""
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Эта команда только для админа!")
        return
    
    session = get_session()
    
    gifts = session.query(Gift).all()
    total_wins = session.query(Win).count()
    pending_wins = session.query(Win).filter_by(status='pending').count()
    
    message = "📊 СТАТИСТИКА\n\n"
    message += f"🎁 Подарки в пуле:\n"
    
    for gift in gifts:
        message += f"{gift.emoji} {gift.name} - {gift.quantity} шт ({gift.rarity})\n"
    
    message += f"\n📈 Всего выигрышей: {total_wins}\n"
    message += f"⏳ Ожидают отправки: {pending_wins}"
    
    session.close()
    
    await update.message.reply_text(message)


def main():
    """Запуск бота"""
    # Инициализируем БД
    logger.info("🗄️ Initializing database...")
    init_db()
    add_initial_gifts()
    
    # Создаём приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_gift", add_gift_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(MessageHandler(filters.Dice.SLOT_MACHINE, handle_dice))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    
    # Запускаем бота
    logger.info("🤖 Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()