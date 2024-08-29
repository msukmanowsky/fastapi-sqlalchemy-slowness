import sqlalchemy as sa
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

sync_engine = sa.create_engine(
    "sqlite:///./db.sqlite3",
    # Set to True to see queries
    echo=False,
)
sync_session_factory = sessionmaker(bind=sync_engine, expire_on_commit=False)

async_engine = create_async_engine(
    "sqlite+aiosqlite:///./db.sqlite3",
    # Set to True to see queries
    echo=False,
)
async_session_factory = async_sessionmaker(bind=async_engine, expire_on_commit=False)
