"""
Eleos Database Connection & Session Management
"""

import os
from pathlib import Path
from typing import Generator, AsyncGenerator
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Load .env file from project root if present
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Connection parameters
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "eleos")

DEFAULT_SYNC_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
DEFAULT_ASYNC_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SYNC_URL)
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL", DEFAULT_ASYNC_URL)

# If DATABASE_URL was provided using postgres://, fix for SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Synchronous Engine & Session
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def _format_async_db_url(url: str, explicit_async_url: str = "") -> str:
    if explicit_async_url and "asyncpg" in explicit_async_url:
        return explicit_async_url
    target = explicit_async_url or url
    if target.startswith("postgresql+asyncpg://"):
        return target
    if target.startswith("postgresql+psycopg2://"):
        return target.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    if target.startswith("postgresql://"):
        return target.replace("postgresql://", "postgresql+asyncpg://", 1)
    if target.startswith("postgres://"):
        return target.replace("postgres://", "postgresql+asyncpg://", 1)
    return target


# Asynchronous Engine & Session (for FastAPI endpoints)
async_engine = create_async_engine(
    _format_async_db_url(DATABASE_URL, ASYNC_DATABASE_URL),
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI or scripts to get synchronous database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI async endpoints to get asynchronous database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

