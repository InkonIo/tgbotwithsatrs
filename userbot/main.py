"""
Userbot for sending gifts (@Lowatje) - using Telethon
Listens for stickers and sends gifts to winners from database
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient, events
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import get_session, Win, Gift

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Userbot credentials
API_ID = int(os.getenv('USERBOT_API_ID'))
API_HASH = os.getenv('USERBOT_API_HASH')
PHONE = os.getenv('USERBOT_PHONE')

# Create client
client = TelegramClient('gift_sender', API_ID, API_HASH)


@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def handle_incoming_message(event):
    """Обработчик входящих личных сообщений"""
    sender = await event.get_sender()
    
    logger.info(f"Received message from {sender.id} (@{sender.username})")
    
    # Если пользователь отправил стикер
    if event.message.sticker:
        logger.info(f"User {sender.id} sent sticker. Checking database...")
        
        # Проверяем БД - есть ли у этого пользователя pending приз
        session = get_session()
        
        pending_win = session.query(Win).join(Gift).filter(
            Win.telegram_user_id == sender.id,
            Win.status == 'pending'
        ).first()
        
        if pending_win:
            # Есть приз!
            gift = pending_win.gift
            
            logger.info(f"Found pending gift for user {sender.id}: {gift.name}")
            
            # Отправляем эмодзи подарка (пока без реального)
            await event.reply(
                f"🎁 Поздравляем!\n\n"
                f"Ваш подарок: {gift.emoji} {gift.name}!\n\n"
                f"✨ Приз отправлен! 🎉\n\n"
                f"(Пока это эмодзи, когда у меня появятся реальные подарки "
                f"в Telegram - они будут отправляться автоматически)"
            )
            
            # Обновляем статус в БД
            pending_win.status = 'sent'
            pending_win.sent_at = datetime.utcnow()
            session.commit()
            
            logger.info(f"Gift {gift.name} sent to user {sender.id}")
            
        else:
            # Нет приза
            logger.info(f"No pending gift for user {sender.id}")
            
            await event.reply(
                "🤔 Похоже, у вас пока нет выигрышей!\n\n"
                "Чтобы получить приз:\n"
                "1. Выбейте джекпот 777 в боте\n"
                "2. Покрутите рулетку призов\n"
                "3. Отправьте мне стикер\n\n"
                "Удачи! 🍀"
            )
        
        session.close()


async def main():
    """Запуск userbot"""
    logger.info("🤖 Userbot starting...")
    logger.info(f"📱 Phone: {PHONE}")
    logger.info(f"🆔 API ID: {API_ID}")
    
    # Запускаем клиент
    await client.start(phone=PHONE)
    
    logger.info("✅ Userbot is running!")
    logger.info("Waiting for messages...")
    
    # Держим бота запущенным
    await client.run_until_disconnected()


if __name__ == '__main__':
    client.loop.run_until_complete(main())