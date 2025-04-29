# tests/test_db.py
import os
import pytest
import pytest_asyncio
from datetime import date
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

import data.requests as requests
from data.models import Base, User, DailyEntry
from config import DATABASE_URL

# --- Async fixture for engine ---
@pytest_asyncio.fixture(scope="module")
async def pg_engine():
    """
    Create and yield an AsyncEngine against PostgreSQL.
    """
    engine = create_async_engine(DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()

# --- Async fixture to prepare schema ---
@pytest_asyncio.fixture(scope="module")
async def prepare_db(pg_engine):
    """
    Drop & recreate all tables before tests run.
    """
    async with pg_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    # optional teardown
    async with pg_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# --- Sync fixture to override sessionmaker ---
@pytest.fixture(autouse=True)
def override_sessionmaker(monkeypatch, pg_engine):
    """
    Monkey-patch requests.async_session to use the pg_engine above.
    """
    TestSession = sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    monkeypatch.setattr(requests, "async_session", TestSession)

# --- Tests ---
@pytest.mark.asyncio
async def test_postgres_connection(pg_engine):
    """
    Smoke test: can we SELECT 1?
    """
    async with pg_engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar_one() == 1

@pytest.mark.asyncio
async def test_add_and_get_user(prepare_db):
    """
    Test adding and retrieving a user.
    """
    tg_id = 4242
    await requests.add_user(tg_id, "testuser", 9999)

    user = await requests.get_user(tg_id)
    assert user is not None
    assert user.tg_id == tg_id
    assert user.tg_user_name == "testuser"
    assert user.user_chat_id == 9999

@pytest.mark.asyncio
async def test_add_and_query_daily_entries(prepare_db):
    """
    Test CRUD for daily entries.
    """
    # Ensure user exists
    tg_id = 1234
    await requests.add_user(tg_id, "entrytester", 5678)
    user = await requests.get_user(tg_id)
    assert user is not None

    # Insert one daily entry
    entry_date = date.today()
    payload = {
        "sleep_hours": 7,
        "sleep_quality": 4,
        "water_liters": 2.5,
        "sport_hours": 1.0,
        "food_quality": 3,
        "vitamins": 1,
        "productivity": 5
    }
    await requests.add_daily_entry(user.id, entry_date, payload)

    # Query all entries
    entries = await requests.get_daily_entries_for_user(user.id)
    assert len(entries) == 1
    e = entries[0]
    assert e.user_id == user.id
    assert e.entry_date == entry_date
    assert e.data == payload

    # Query by date
    one = await requests.get_daily_entry_by_date(user.id, entry_date)
    assert one is not None
    assert one.id == e.id
    # Nonexistent date
    none = await requests.get_daily_entry_by_date(user.id, entry_date.replace(day=entry_date.day-1))
    assert none is None
