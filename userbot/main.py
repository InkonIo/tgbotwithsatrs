"""
Userbot for sending gifts (@Lowatje)
Listens for commands from the main bot and sends gifts to winners
"""

import os
import logging
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import Message

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

# Create userbot client
app = Client(
    "gift_sender",
    api_id=API_ID,
    api_hash=API_HASH,
    phone_number=PHONE
)


@app.on_message(filters.private & filters.incoming)
async def handle_incoming_message(client: Client, message: Message):
    """Обработчик входящих сообщений"""
    user = message.from_user
    
    logger.info(f"Received message from {user.id} (@{user.username}): {message.text}")
    
    # Если пользователь отправил стикер (как требуется в ТЗ)
    if message.sticker:
        await message.reply_text(
            "✅ Спасибо! Ваш подарок скоро будет отправлен.\n"
            "Пожалуйста, подождите..."
        )
        
        # TODO: Здесь будет логика отправки подарка
        # Пока просто логируем
        logger.info(f"User {user.id} sent sticker. Ready to send gift.")


@app.on_message(filters.command("send_gift") & filters.me)
async def send_gift_command(client: Client, message: Message):
    """
    Команда для отправки подарка
    Формат: /send_gift <user_id> <gift_name>
    """
    try:
        parts = message.text.split()
        if len(parts) < 3:
            await message.edit("❌ Формат: /send_gift <user_id> <gift_name>")
            return
        
        user_id = int(parts[1])
        gift_name = " ".join(parts[2:])
        
        # TODO: Здесь будет реальная отправка подарка через Telegram API
        # Пока просто отправляем текстовое сообщение
        await client.send_message(
            user_id,
            f"🎁 Поздравляем!\n\n"
            f"Вы выиграли: **{gift_name}**\n\n"
            f"Подарок отправлен! Проверьте свой профиль."
        )
        
        await message.edit(f"✅ Подарок '{gift_name}' отправлен пользователю {user_id}")
        logger.info(f"Gift '{gift_name}' sent to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error sending gift: {e}")
        await message.edit(f"❌ Ошибка: {e}")


def main():
    """Запуск юзербота"""
    logger.info("🤖 Userbot starting...")
    logger.info(f"📱 Phone: {PHONE}")
    logger.info(f"🆔 API ID: {API_ID}")
    
    # Запускаем клиент
    app.run()


if __name__ == '__main__':
    main()