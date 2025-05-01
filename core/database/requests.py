from .models import async_session, DailyEntry, User, Experiment, Parameter
from sqlalchemy import select


async def add_experiment(user_id: int, name: str) -> Experiment:
    async with async_session() as session:
        experiment = Experiment(user_id=user_id, name=name)
        session.add(experiment)
        await session.commit()
        return experiment


async def get_list_experiments(user_id: int) -> list[Experiment]:
    async with async_session() as session:
        rows = await session.scalars(
            select(Experiment).where(Experiment.user_id == user_id)
        )
        return rows.all()


async def add_parameter(
    user_id, name, is_goal, ptype, exp_id, class_min=None, class_max=None
):
    async with async_session() as session:
        param = Parameter(
            user_id=user_id,
            experiment_id=exp_id,
            name=name,
            is_goal=is_goal,
            type=ptype,
            class_min=class_min,
            class_max=class_max,
        )
        session.add(param)
        await session.commit()
        return param


async def get_list_parameters(exp_id: int) -> list[Parameter]:
    async with async_session() as session:
        rows = await session.scalars(
            select(Parameter).where(Parameter.experiment_id == exp_id)
        )
        return rows.all()


async def add_daily_entry(user_id: int, entry_date, data: dict) -> None:
    async with async_session() as session:
        # Optionally, you might want to check for an existing entry for the same day if unique constraint is enforced.
        new_entry = DailyEntry(user_id=user_id, entry_date=entry_date , data=data)
        session.add(new_entry)
        await session.commit()


async def get_daily_entries_for_user(user_id: int):
    """
    Returns:
        A list of DailyEntry objects.
    """
    async with async_session() as session:
        result = await session.scalars(select(DailyEntry).where(DailyEntry.user_id == user_id))
        return result.all()


async def get_daily_entry_by_date(user_id: int, entry_date):
    """
    Returns:
        A DailyEntry object or None if no entry is found.
    """
    async with async_session() as session:
        entry = await session.scalar(
            select(DailyEntry).where(
                DailyEntry.user_id == user_id,
                DailyEntry.entry_date == entry_date
            )
        )
        return entry


async def add_user(tg_id: int, tg_user_name: str, user_chat_id: int) -> None:
    async with async_session() as session:
        # Check if the user already exists based on Telegram ID
        existing_user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if existing_user is None:
            new_user = User(tg_id=tg_id, username=tg_user_name, user_chat_id=user_chat_id)
            session.add(new_user)
            await session.commit()


async def get_user(tg_id: int) -> User:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        return user