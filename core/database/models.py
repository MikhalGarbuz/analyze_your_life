import enum

from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey, UniqueConstraint, Boolean, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker
from config import DATABASE_URL



engine = create_async_engine(DATABASE_URL, echo=True)

async_session = async_sessionmaker(engine)


Base = declarative_base()

class ParamType(enum.Enum):
    BOOLEAN = "boolean"
    CLASS   = "class"
    NUMERIC = "numeric"

class Experiment(Base):
    __tablename__ = "experiments"

    id       = Column(Integer, primary_key=True)
    user_id  = Column(Integer, ForeignKey("users.id"), nullable=False)
    name     = Column(String, nullable=False)

    user         = relationship("User", back_populates="experiments")
    parameters   = relationship("Parameter", back_populates="experiment")

User.experiments = relationship("Experiment", back_populates="user")

class Parameter(Base):
    __tablename__ = "parameters"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)

    name = Column(String, nullable=False)
    is_goal = Column(Boolean, default=False, nullable=False)
    type = Column(Enum(ParamType, name="param_type"), nullable=False)
    experiment = relationship("Experiment", back_populates="parameters")


class User(Base):
    __tablename__ = "users"

    tg_id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)

    # # Optionally, store configuration in a JSONB column
    # configuration = Column(JSONB, nullable=True)
    user_chat_id = Column(Integer)

    # Relationship with daily entries
    daily_entries = relationship("DailyEntry", back_populates="user")
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


# Daily entries table
class DailyEntry(Base):
    __tablename__ = "daily_entries"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.tg_id"), nullable=False)
    entry_date = Column(Date, nullable=False)
    data = Column(JSONB, nullable=False)

    # Optional unique constraint to ensure one entry per day per user
    __table_args__ = (UniqueConstraint("user_id", "entry_date", name="_user_date_uc"),)

    user = relationship("User", back_populates="daily_entries")

    def __repr__(self):
        return f"<DailyEntry(id={self.id}, user_id={self.user_id}, entry_date={self.entry_date})>"

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)