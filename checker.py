import aiohttp
import asyncio

URL = "https://api-my.sa.gov.ge/api/v1/DrivingLicensePracticalExams2/DrivingLicenseExamsDates2?CategoryCode=4&CenterId=7"

previous_slots = set()

async def fetch_slots():
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as response:
            data = await response.json()
            return {(d['ExamDate'], d['FreePlaceCount']) for d in data}

async def check_for_new_slots(send_callback):
    global previous_slots
    while True:
        try:
            new_slots = await fetch_slots()
            if new_slots - previous_slots:
                # Новые слоты появились
                previous_slots = new_slots
                pretty = '\n'.join(f"{date}: {count} мест" for date, count in sorted(new_slots))
                await send_callback(pretty)
        except Exception as e:
            print(f"Ошибка в checker: {e}")
        await asyncio.sleep(120)
