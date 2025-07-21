import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message , FSInputFile
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from database import init_db, add_user, get_all_users
from checker import check_for_new_slots, get_initial_slots
from checker import fetch_slots, format_slots, previous_slots


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import toggle_subscription, get_user_subscriptions
from checker import CITIES



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
    photo = FSInputFile("welcome.jpg")
    await bot.send_photo(
        chat_id=message.chat.id,
        photo=photo,
        caption=(
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
def get_city_keyboard(subscribed: list[str]) -> InlineKeyboardMarkup:
    buttons = []
    for city in CITIES.keys():
        is_subscribed = city in subscribed
        label = f"{'🟢' if is_subscribed else '⚪'} {city}"
        buttons.append(
            [InlineKeyboardButton(text=label, callback_data=f"toggle_{city}")]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    subs = await get_user_subscriptions(message.from_user.id)
    kb = get_city_keyboard(subs)
    await message.answer("🔔 Выберите города для подписки:", reply_markup=kb)

@dp.callback_query(F.data.startswith("toggle_"))
async def cb_toggle_city(callback: CallbackQuery):
    city = callback.data.replace("toggle_", "")
    await toggle_subscription(callback.from_user.id, city)
    subs = await get_user_subscriptions(callback.from_user.id)
    kb = get_city_keyboard(subs)
    await callback.message.edit_text("🔔 Выберите города для подписки:", reply_markup=kb)
    
@dp.message(Command("slots"))
async def cmd_slots(message: Message):
    result = await get_initial_slots()
    await message.answer(f"📅 <b>Актуальные слоты:</b>\n\n{result}")

async def send_callback(user_id: int, text: str):
    await bot.send_message(user_id, f"📢 <b>Новые даты:</b>\n\n{text}")

async def on_startup():
    await init_db()
    print("[DEBUG] Загружаем начальные слоты...")
    all_slots = {}  # кеш всех городов
    for city, url in CITIES.items():
        try:
            slots = await fetch_slots(url)
            all_slots[city] = slots
        except Exception as e:
            print(f"[ERROR] Ошибка при загрузке слотов {city}: {e}")
            all_slots[city] = set()

    # Сохраняем в глобальный previous_slots
    from checker import previous_slots
    previous_slots.update(all_slots)

    users = await get_all_users()
    for user_id in users:
        user_cities = await get_user_subscriptions(user_id)
        user_text_blocks = []
        for city in user_cities:
            city_slots = all_slots.get(city, set())
            if city_slots:
                formatted = format_slots(city_slots)
                user_text_blocks.append(f"<b>{city}</b>\n{formatted}")
        if user_text_blocks:
            try:
                await send_callback(user_id, "📅 <b>Актуальные слоты:</b>\n\n" + "\n\n".join(user_text_blocks))
            except Exception as e:
                print(f"[ERROR] Не удалось отправить сообщение {user_id}: {e}")

    asyncio.create_task(check_for_new_slots(send_callback))

if __name__ == "__main__":
    dp.startup.register(on_startup)
    dp.run_polling(bot)
