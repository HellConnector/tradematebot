from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

import bot.settings as settings
from .data_helper import (
    get_stats_data,
    get_tracking_data,
    get_tracking_records,
    get_tracking_records_for_user,
)
from .models import (
    Base,
    Client,
    Deal,
    Item,
    Skin,
    Container,
    Tool,
    Price,
    PriceLimit,
    Sticker,
    Agent,
    TrackingRecord,
    SearchItem,
)

DB_ADDR = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
    f"{settings.POSTGRES_HOST}/{settings.POSTGRES_DB}"
)

async_engine = create_async_engine(
    DB_ADDR, echo=False, pool_pre_ping=True, pool_size=20, max_overflow=20
)


@asynccontextmanager
async def get_async_session(**kwargs) -> AsyncGenerator[AsyncSession, Any]:
    session = AsyncSession(bind=async_engine, expire_on_commit=False, **kwargs)
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


__all__ = (
    "Base",
    "Client",
    "Deal",
    "Item",
    "Skin",
    "Container",
    "Tool",
    "Price",
    "PriceLimit",
    "Sticker",
    "Agent",
    "TrackingRecord",
    "SearchItem",
    "get_async_session",
    "DB_ADDR",
    "get_stats_data",
    "get_tracking_data",
    "get_tracking_records",
    "get_tracking_records_for_user",
)
