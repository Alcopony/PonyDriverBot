
import aiosqlite

DB_PATH = "users.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER,
                city TEXT,
                UNIQUE(user_id, city)
            )
        """)
        await db.commit()

async def add_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await db.commit()

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id FROM users")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def get_user_subscriptions(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT city FROM subscriptions WHERE user_id = ?", (user_id,))
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def toggle_subscription(user_id: int, city: str):
    async with aiosqlite.connect(DB_PATH) as db:
        subs = await get_user_subscriptions(user_id)
        if city in subs:
            await db.execute("DELETE FROM subscriptions WHERE user_id = ? AND city = ?", (user_id, city))
        else:
            await db.execute("INSERT OR IGNORE INTO subscriptions (user_id, city) VALUES (?, ?)", (user_id, city))
        await db.commit()

async def get_all_subscribed_users_by_city(city: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id FROM subscriptions WHERE city = ?", (city,))
        rows = await cursor.fetchall()
        return [row[0] for row in rows]
