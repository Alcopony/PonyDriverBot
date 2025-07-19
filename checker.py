import aiohttp
import asyncio
from datetime import datetime

CITIES = {
    "Гори": "https://api-my.sa.gov.ge/api/v1/DrivingLicensePracticalExams2/DrivingLicenseExamsDates2?CategoryCode=4&CenterId=7",
    "Батуми": "https://api-my.sa.gov.ge/api/v1/DrivingLicensePracticalExams2/DrivingLicenseExamsDates2?CategoryCode=4&CenterId=3",
}

previous_slots = {city: set() for city in CITIES}

def format_slots(slots: set[tuple[str, int]]) -> str:
    rows = []
    for date_str, count in sorted(slots):
        date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
        weekday = date_obj.strftime('%A')
        rows.append(f"{date_obj.strftime('%d.%m.%Y')} ({weekday}): {count} мест")
    return "\n".join(rows)

async def fetch_slots(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            return {(d['ExamDate'], d['FreePlaceCount']) for d in data}

async def get_initial_slots() -> str:
    global previous_slots
    blocks = []
    for city, url in CITIES.items():
        try:
            slots = await fetch_slots(url)
            print(f"[DEBUG] {city}: {len(slots)} слотов получено")
            previous_slots[city] = slots  # сохраняем состояние
            if slots:
                formatted = format_slots(slots)
                blocks.append(f"<b>{city}</b>\n{formatted}")
            else:
                blocks.append(f"<b>{city}</b>\nНет доступных слотов.")
        except Exception as e:
            print(f"[ERROR] Ошибка при загрузке слотов для {city}: {e}")
            blocks.append(f"<b>{city}</b>\nОшибка при получении данных.")
    return "\n\n".join(blocks)

async def check_for_new_slots(send_callback):
    global previous_slots
    while True:
        try:
            combined_updates = []
            for city, url in CITIES.items():
                new_slots = await fetch_slots(url)
                if new_slots - previous_slots[city]:
                    previous_slots[city] = new_slots
                    formatted = format_slots(new_slots)
                    combined_updates.append(f"<b>{city}</b>\n{formatted}")
            if combined_updates:
                await send_callback("\n\n".join(combined_updates))
        except Exception as e:
            print(f"Ошибка в checker: {e}")
        await asyncio.sleep(120)
