import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from database import init_db, add_user, get_all_users
from checker import check_for_new_slots, get_initial_slots

load_dotenv()
logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=os.getenv("BOT_TOKEN"),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await add_user(message.from_user.id)

    # отправка локальной картинки
    with open("welcome.jpg", "rb") as photo:
        await bot.send_photo(message.chat.id, photo, caption=(
            "👋 <b>Добро пожаловать маленькое пони!</b>\n\n"
            "Ты подписалась на уведомления о новых слотах для экзамена на водительское удостоверение.\n\n"
            "📅 Используйте команду /slots чтобы вручную проверить доступные даты."
            "Хороших погод и подкованных копытц!"
        ))

    # лог
    users = await get_all_users()
    print(f"[DEBUG] Зарегистрированные пользователи: {users}")

    # отправим актуальные слоты
    initial_data = await get_initial_slots()
    await message.answer(f"📅 <b>Актуальные слоты:</b>\n\n{initial_data}")

    # Выведем список подписчиков в лог
    users = await get_all_users()
    print(f"[DEBUG] Зарегистрированные пользователи: {users}")

@dp.message(Command("slots"))
async def cmd_slots(message: Message):
    result = await get_initial_slots()
    await message.answer(f"📅 <b>Актуальные слоты:</b>\n\n{result}")

async def send_to_all_users(text):
    users = await get_all_users()
    print(f"[DEBUG] Отправляем {len(users)} пользователям сообщение:\n{text}")
    for uid in users:
        try:
            await bot.send_message(uid, f"📢 <b>Новые даты экзаменов!</b>\n\n{text}")
            print(f"[DEBUG] Успешно отправлено {uid}")
        except Exception as e:
            print(f"[ERROR] Не удалось отправить сообщение пользователю {uid}: {e}")

async def on_startup():
    await init_db()
    print("[DEBUG] Загружаем начальные слоты...")
    initial_data = await get_initial_slots()
    print(f"[DEBUG] Слоты загружены:\n{initial_data}")
    await send_to_all_users(f"Актуальные слоты:\n\n{initial_data}")
    asyncio.create_task(check_for_new_slots(send_to_all_users))

if __name__ == "__main__":
    dp.startup.register(on_startup)
    dp.run_polling(bot)
