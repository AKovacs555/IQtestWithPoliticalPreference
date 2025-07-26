import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, JSON

DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite+aiosqlite:///./test.db"

# Convert plain Postgres URLs to asyncpg syntax for create_async_engine
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql+psycopg2://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, future=True, echo=False)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    hashed_id = Column(String, primary_key=True, index=True)
    salt = Column(String, nullable=False)
    plays = Column(Integer, default=0)
    referrals = Column(Integer, default=0)
    points = Column(Integer, default=0)
    scores = Column(JSON, default=list)
    party_log = Column(JSON, default=list)
    party_ids = Column(JSON, default=list)
    demographics = Column(JSON, default=dict)
    variant = Column(Integer, nullable=True)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
