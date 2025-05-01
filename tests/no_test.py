from core.database.requests import add_user, add_daily_entry
from datetime import date
import asyncio


async def main():
    tg_user_id = 123

    await add_user(tg_user_id, "user1", 456)

    daily_input = {
        "sleep_hours": 7,
        "sleep_quality": 4,
        "water_liters": 2.5,
        "sport_hours": 1.0,
        "food_quality": 3,
        "vitamins": 1,
        "productivity": 5
    }

    entry_date = date.today()

    await add_daily_entry(tg_user_id, entry_date, daily_input)

if __name__ == "__main__":
    asyncio.run(main())