# bot/utils.py
from datetime import date
from sqlalchemy import select

from core.database.models import User, DailyEntry
from core.database.requests import async_session
from aiogram import Bot

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

async def remind_missing_entries(bot: Bot):
    today = date.today()
    async with async_session() as session:
        # load every user
        users = (await session.scalars(select(User))).all()

        for user in users:
            # for each, check if they’ve entered today’s data
            stmt = select(DailyEntry).where(
                DailyEntry.user_id == user.id,
                DailyEntry.experiment_id != None,   # optional: only for existing experiments
                DailyEntry.entry_date == today
            )
            entry = await session.scalar(stmt)
            if entry is None:
                # no entry → send reminder
                await bot.send_message(
                    chat_id=user.user_chat_id,
                    text=(
                        "👋 Привіт! Здається, ви ще не ввели сьогоднішні дані. "
                        "Будь ласка, /enter або /enter_past, щоб додати їх."
                    )
                )

def make_scheduler(bot: Bot) -> AsyncIOScheduler:

    scheduler = AsyncIOScheduler(bot)
    # every day at 19:00 local time
    scheduler.add_job(
        remind_missing_entries,
        CronTrigger(hour=19, minute=0),
        args=(bot,),
        id="daily_reminder",
        replace_existing=True,
    )
    return scheduler