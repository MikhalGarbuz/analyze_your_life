import asyncio
import logging
from core.database.models import async_main

from aiogram import Bot, Dispatcher

from bot.handlers.handlers import router
from bot.daily_reminder import make_scheduler
from config import TOKEN


bot = Bot(token=TOKEN)
dp = Dispatcher()


async def main():
    await async_main()
    dp.include_router(router)

    scheduler = make_scheduler(bot)
    scheduler.start()

    await dp.start_polling(bot)


if __name__ =='__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')