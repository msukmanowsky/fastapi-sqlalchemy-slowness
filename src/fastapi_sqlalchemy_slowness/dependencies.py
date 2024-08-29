import typing as T

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .database import async_session_factory, sync_session_factory


async def get_async_db_session():
    async with async_session_factory() as session:
        yield session


AsyncDBSessionDep = T.Annotated[AsyncSession, Depends(get_async_db_session)]


def get_sync_db_session():
    with sync_session_factory() as session:
        yield session


SyncDBSessionDep = T.Annotated[AsyncSession, Depends(get_sync_db_session)]
