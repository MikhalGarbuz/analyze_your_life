import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.handlers import router


bot = Bot(token="7265040908:AAHGXHGM84GQ9fn5w4YpqZZyuQvXaPyUSUk")
dp = Dispatcher()


async def main():
    #await async_main() for using database
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ =='__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')