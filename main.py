from telethon import TelegramClient, events, types
import asyncio
import os

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_USERNAME = os.getenv('CHAT_USERNAME')
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')

TARGET_CHAT_ID = None

bot = TelegramClient('bot_session', API_ID, API_HASH, device_model="Web")
user = TelegramClient('user_session', API_ID, API_HASH, device_model="Web")
keywords = ["видеокарт", "блок питания", "блоки питания"]

@bot.on(events.NewMessage(pattern='/keywords'))
async def keywords_handler(event):
    sender = await event.get_sender()

    if sender.username != CHAT_USERNAME:
        await event.respond("⚠️ У вас нет доступа к этому боту.")
        print(f"Попытка доступа от неавторизованного пользователя: @{sender.username}")
        return

    keywords_text = "\n".join([f"• {keyword}" for keyword in keywords])
    await event.respond(
        "📝 Текущий список ключевых слов:\n\n"
        f"{keywords_text}\n\n"
        "Бот будет пересылать сообщения, содержащие эти ключевые слова."
    )
    print(f"Список ключевых слов отправлен пользователю @{sender.username}")

@user.on(events.NewMessage(chats=CHANNEL_USERNAME))
async def new_message_handler(event):
    message = event.message
    print(f"Новое сообщение в канале: {message.text}")

    if TARGET_CHAT_ID and message.text and any(keyword in message.text.lower() for keyword in keywords):
        channel = await user.get_entity(message.peer_id)
        forward_message = await user.get_messages(channel, ids=[message.id])
        bot_channel = await bot.get_entity(CHANNEL_USERNAME)
        await bot.forward_messages(TARGET_CHAT_ID, forward_message[0], from_peer=bot_channel)
        matched_keywords = [k for k in keywords if k in message.text.lower()]
        print(f"Сообщение с упоминанием '{', '.join(matched_keywords)}' переслано в чат {TARGET_CHAT_ID}")

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    sender = await event.get_sender()

    if sender.username != CHAT_USERNAME:
        await event.respond("⚠️ У вас нет доступа к этому боту.")
        print(f"Попытка доступа от неавторизованного пользователя: @{sender.username}")
        return
    
    global TARGET_CHAT_ID
    TARGET_CHAT_ID = event.chat_id
    
    keyboard = [[types.KeyboardButton(text='/keywords')]]
    
    await event.respond(
        "👋 Привет! Я бот для пересылки сообщений из канала.\n\n"
        f"Я буду пересылать все новые сообщения из канала @{CHANNEL_USERNAME} "
        "прямо в этот чат.\n\n"
        "Теперь вы не пропустите ни одного обновления! 🚀\n\n"
        "Нажмите /keywords чтобы увидеть список ключевых слов",
        buttons=keyboard
    )

    print(f"Бот успешно запущен пользователем @{sender.username}")
async def main():
    try:
        print("Запуск бота...")
        await bot.start(bot_token=BOT_TOKEN)

        print("Запуск пользователя...")
        await user.start()

        if not await user.is_user_authorized():
            print("Требуется авторизация. Следуйте инструкциям в консоли.")
            await user.send_code_request(phone=input("Введите номер телефона: "))
            await user.sign_in(code=input("Введите код подтверждения: "))
        
        print("Система успешно запущена!")
        await asyncio.gather(
            bot.run_until_disconnected(),
            user.run_until_disconnected(),
            return_exceptions=True
        )
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        await bot.disconnect()
        await user.disconnect()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
