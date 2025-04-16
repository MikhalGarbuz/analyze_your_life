from models import async_session, DailyEntry, User
from sqlalchemy import select


async def add_daily_entry(user_id: int, entry_date, data: dict) -> None:
    """
    Adds a new daily entry for a user.

    Parameters:
        user_id (int): The ID of the user.
        entry_date: The date of the entry (can be a datetime.date or similar).
        data (dict): A dictionary of daily variable values.

    Returns:
        None
    """
    async with async_session() as session:
        # Optionally, you might want to check for an existing entry for the same day if unique constraint is enforced.
        new_entry = DailyEntry(user_id=user_id, entry_date=entry_date , data=data)
        session.add(new_entry)
        await session.commit()


async def get_daily_entries_for_user(user_id: int):
    """
    Retrieves all daily entries for a given user.

    Parameters:
        user_id (int): The ID of the user.

    Returns:
        A list of DailyEntry objects.
    """
    async with async_session() as session:
        result = await session.scalars(select(DailyEntry).where(DailyEntry.user_id == user_id))
        return result.all()


async def get_daily_entry_by_date(user_id: int, entry_date):
    """
    Retrieves the daily entry for a specific user on a specific date.

    Parameters:
        user_id (int): The ID of the user.
        entry_date: The date for which to retrieve the entry.

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
    """
    Adds a new user to the database if a user with the given tg_id doesn't exist.

    Parameters:
        tg_id (int): The Telegram ID of the user.
        tg_user_name (str): The Telegram username.
        user_chat_id (int): The chat ID for the user.

    Returns:
        None
    """
    async with async_session() as session:
        # Check if the user already exists based on Telegram ID
        existing_user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if existing_user is None:
            new_user = User(tg_id=tg_id, tg_user_name=tg_user_name, user_chat_id=user_chat_id)
            session.add(new_user)
            await session.commit()


async def get_user(tg_id: int) -> User:
    """
    Retrieves a user from the database based on the provided Telegram ID.

    Parameters:
        tg_id (int): The Telegram ID of the user.

    Returns:
        User: The user object if found, otherwise None.
    """
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        return user