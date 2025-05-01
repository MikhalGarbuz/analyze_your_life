import pytest
import pytest_asyncio
from datetime import date
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL
from core.database.models import Base
import core.database.requests as requests
from core.database.requests import add_user, get_user

@pytest.mark.asyncio
async def test_postgres_connection():
    """
    Can we connect to Postgres and run a trivial query?
    """
    engine = create_async_engine(DATABASE_URL, echo=False)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar_one() == 1
    finally:
        await engine.dispose()


# --- Async fixture: engine + clean schema for user tests ---
@pytest_asyncio.fixture
async def pg_engine():
    engine = create_async_engine(DATABASE_URL, echo=False)
    # Create tables once before any tests in this module
    async with engine.begin() as conn:
        # Ensure clean slate for users table
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine

    # teardown: drop all tables to clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    # finally dispose the engine

    await engine.dispose()

# --- Sync fixture: patch async_session to use our test engine ---
@pytest.fixture(autouse=True)
def override_sessionmaker(monkeypatch, pg_engine):
    TestSession = sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    # patch the session factory in your requests module
    monkeypatch.setattr("data.requests.async_session", TestSession)

# —————————————————————————————
# Step 2 Test: add_user & get_user
# —————————————————————————————
@pytest.mark.asyncio
async def test_add_and_get_user(pg_engine):
    # 1) No user at first:
    assert await get_user(9999) is None

    # 2) Add a user
    tg_id = 4242
    await add_user(tg_id, "testuser", 12345)

    # 3) Retrieve it back
    user = await get_user(tg_id)
    assert user is not None
    assert user.tg_id == tg_id
    assert user.username == "testuser"
    assert user.user_chat_id == 12345

    # 4) Calling add_user again with same tg_id shouldn't raise or create duplicates
    await add_user(tg_id, "testuser", 12345)
    # Verify still only one row in users table:
    async with pg_engine.connect() as conn:
        result = await conn.execute(text("SELECT count(*) FROM users"))
        assert result.scalar_one() == 1


# — Test 1: no entries for a brand-new user —————————————
@pytest.mark.asyncio
async def test_no_daily_entries_for_new_user():
    entries = await requests.get_daily_entries_for_user(user_id=9999)
    assert entries == []


# — Test 2: can add a daily entry and then get it all ——————————
@pytest.mark.asyncio
async def test_add_and_get_all_daily_entries():
    uid = 1001
    await requests.add_user(uid, "daily_all", 111)
    today = date.today()
    payload = {
        "sleep_hours": 6.5,
        "sleep_quality": 3,
        "water_liters": 2.2,
        "sport_hours": 0.5,
        "food_quality": 4,
        "vitamins": 1,
        "productivity": 4
    }
    await requests.add_daily_entry(uid, today, payload)

    all_entries = await requests.get_daily_entries_for_user(uid)
    assert len(all_entries) == 1
    entry = all_entries[0]
    assert entry.user_id == uid
    assert entry.entry_date == today
    assert entry.data == payload


# — Test 3: get_daily_entry_by_date returns the correct row ——————
@pytest.mark.asyncio
async def test_get_daily_entry_by_exact_date():
    uid = 1002
    await requests.add_user(uid, "daily_exact", 222)
    target_date = date.today()
    payload = {"foo": "bar"}
    await requests.add_daily_entry(uid, target_date, payload)

    fetched = await requests.get_daily_entry_by_date(uid, target_date)
    assert fetched is not None
    assert fetched.user_id == uid
    assert fetched.entry_date == target_date
    assert fetched.data == payload


# — Test 4: get_daily_entry_by_date returns None when missing ————
@pytest.mark.asyncio
async def test_get_daily_entry_missing_date():
    uid = 1003
    await requests.add_user(uid, "daily_none", 333)
    missing_date = date.today()

    fetched = await requests.get_daily_entry_by_date(uid, missing_date)
    assert fetched is None


# — Test 5: raw SQL count for daily_entries ————————————————
@pytest.mark.asyncio
async def test_raw_sql_count_daily_entries(pg_engine):
    uid = 1004
    await requests.add_user(uid, "daily_count", 444)
    d = date.today()
    pl = {"a": 1}
    await requests.add_daily_entry(uid, d, pl)

    async with pg_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT count(*) FROM daily_entries WHERE user_id = :uid"),
            {"uid": uid}
        )
        assert result.scalar_one() == 1