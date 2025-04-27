# tests/test_requests.py
import pytest
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# import your “requests” module
import data.requests as requests
from data.models import Base, User, DailyEntry

from config import DATABASE_URL
@pytest.fixture(scope="module")
async def setup_db(monkeypatch):
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    monkeypatch.setattr(requests, "async_session", TestSession)
    yield
    await engine.dispose()

@pytest.mark.asyncio
async def test_add_and_get_user(setup_db):
    assert await requests.get_user(9999) is None
    await requests.add_user(1111, "alice", 2222)
    u = await requests.get_user(1111)
    assert u.tg_id == 1111 and u.tg_user_name == "alice"
    # …etc…
