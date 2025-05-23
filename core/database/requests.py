from .models import async_session, DailyEntry, User, Experiment, Parameter
from sqlalchemy import select, delete


async def add_experiment(user_id: int, name: str) -> Experiment:
    async with async_session() as session:
        experiment = Experiment(user_id=user_id, name=name)
        session.add(experiment)
        await session.commit()
        await session.refresh(experiment)
        return experiment

async def get_experiment(experiment_id: int) -> Experiment | None:
    """
    Return the Experiment with the given ID, or None if not found.
    """
    async with async_session() as session:
        return await session.get(Experiment, experiment_id)

async def get_list_experiments(user_id: int) -> list[Experiment]:
    async with async_session() as session:
        rows = await session.scalars(
            select(Experiment).where(Experiment.user_id == user_id)
        )
        return rows.all()

async def delete_experiment(experiment_id: int) -> None:
    """
    Deletes an Experiment and all its related parameters & daily entries.
    Manually cascades deletes in case the database constraint was not applied.
    """
    async with async_session() as session:
        # explicitly remove any parameters and entries tied to this experiment
        await session.execute(
            delete(Parameter).where(Parameter.experiment_id == experiment_id)
        )
        await session.execute(
            delete(DailyEntry).where(DailyEntry.experiment_id == experiment_id)
        )
        # now delete the experiment itself
        exp = await session.get(Experiment, experiment_id)
        if exp:
            await session.delete(exp)
            await session.commit()


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

async def get_parameter(param_id: int) -> Parameter | None:
    """
    Fetches a single Parameter by its primary key.
    """
    async with async_session() as session:
        return await session.get(Parameter, param_id)

async def get_list_parameters(exp_id: int) -> list[Parameter]:
    async with async_session() as session:
        rows = await session.scalars(
            select(Parameter).where(Parameter.experiment_id == exp_id)
        )
        return rows.all()


async def add_daily_entry(user_id: int, experiment_id: int, entry_date, data: dict) -> DailyEntry:
    existing = await get_daily_entry_by_all_conditions(user_id, experiment_id, entry_date)
    async with async_session() as session:

        if existing:
            # 2a) update its JSON payload
            existing.data = data
            entry = existing
        else:
            entry = DailyEntry(user_id=user_id, experiment_id= experiment_id, entry_date=entry_date , data=data)
        session.add(entry)
        await session.commit()
        return entry


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

async def get_daily_entry_by_all_conditions(user_id: int, experiment_id: int, entry_date) -> DailyEntry | None:
    """
    Return the existing DailyEntry for this user+experiment+date,
    or None if none exists.
    """
    async with async_session() as session:
        entry = await session.scalar(
            select(DailyEntry).where(
            DailyEntry.user_id == user_id,
            DailyEntry.experiment_id == experiment_id,
            DailyEntry.entry_date == entry_date
            )
        )
        return entry

async def get_daily_entries_for_experiment(user_id: int, experiment_id: int) -> list[DailyEntry]:
    """
    Return all DailyEntry rows for this user+experiment, ordered by date.
    """
    async with async_session() as session:
        stmt = (
            select(DailyEntry)
            .where(
                DailyEntry.user_id == user_id,
                DailyEntry.experiment_id == experiment_id
            )
            .order_by(DailyEntry.entry_date)
        )
        result = await session.scalars(stmt)
        return result.all()

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

