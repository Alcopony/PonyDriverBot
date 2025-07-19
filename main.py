import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
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
    await message.answer("Пони подписано!")

async def send_to_all_users(text):
    users = await get_all_users()
    for uid in users:
        try:
            await bot.send_message(uid, f"📅 {text}")
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {uid}: {e}")

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
