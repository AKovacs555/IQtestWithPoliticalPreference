import os
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy import (
    Column,
    String,
    JSON,
    BigInteger,
    DateTime,
    func,
)

# Database connection URL must be provided via the environment
DATABASE_URL = os.environ["DATABASE_URL"]

# Convert plain Postgres URLs to asyncpg syntax for create_async_engine
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql+psycopg2://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True,
    echo=False,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    hashed_id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    salt = Column(String, nullable=False)
    plays = Column(BigInteger, default=0)
    points = Column(BigInteger, default=0)
    referrals = Column(BigInteger, default=0)
    scores = Column(JSON, nullable=True)
    party_log = Column(JSON, nullable=True)
    demographic = Column(JSON, nullable=True)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def get_session() -> AsyncSession:
    """Return a new asynchronous SQLAlchemy session."""
    return AsyncSessionLocal()
