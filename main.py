import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from dotenv import load_dotenv
import os

from database import init_db, add_user, get_all_users
from checker import check_for_new_slots

load_dotenv()
logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv("BOT_TOKEN"), parse_mode=ParseMode.HTML)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await add_user(message.from_user.id)
    await message.answer("Вы подписались на уведомления о новых окнах для экзамена на ВУ!")

async def send_to_all_users(text):
    users = await get_all_users()
    for uid in users:
        try:
            await bot.send_message(uid, f"📅 Появились новые слоты!\n\n{text}")
        except Exception as e:
            print(f"Ошибка отправки {uid}: {e}")

async def on_startup():
    await init_db()
    asyncio.create_task(check_for_new_slots(send_to_all_users))

if __name__ == "__main__":
    dp.startup.register(on_startup)
    dp.run_polling(bot)
