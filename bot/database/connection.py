import asyncpg
from typing import Optional

from config import settings

_pool: Optional[asyncpg.Pool] = None

async def get_pool() -> asyncpg.Pool:
    """Возвращает глобальный пул подключений к базе данных PostgreSQL."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=settings.database_url)
    return _pool

async def close_pool() -> None:
    """Закрывает пул при завершении работы приложения."""
    if _pool and not _pool._closed:
        await _pool.close() 