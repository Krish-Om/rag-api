import os
from typing import Generator

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import all models so they are registered with SQLModel.metadata
from app.models import Document, Chunk, Booking

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    default="postgresql://raguser:password123@localhost:5433/document_db",
)

# Create sync URL by removing async driver
if "+asyncpg" in DATABASE_URL:
    sync_url = DATABASE_URL.replace("+asyncpg", "")
    # Async engine for application use (only if asyncpg is in URL)
    async_engine = create_async_engine(DATABASE_URL, echo=True)
    async_session_maker = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
else:
    sync_url = DATABASE_URL
    async_engine = None
    async_session_maker = None

# Sync engine for table creation
sync_engine = create_engine(sync_url, echo=True)


def create_db_and_tables():
    """Create tables using sync engine"""
    SQLModel.metadata.create_all(sync_engine)


def get_session() -> Generator[Session, None, None]:
    """Legacy sync session - prefer get_async_session"""
    with Session(sync_engine) as session:
        yield session


async def get_async_session() -> Generator[AsyncSession, None, None]:
    """Get async session for database operations"""
    async with async_session_maker() as session:
        yield session


def init_db():
    """Initialize database - safe to call from sync context"""
    create_db_and_tables()
