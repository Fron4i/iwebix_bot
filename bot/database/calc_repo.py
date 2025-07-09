import asyncpg
from typing import Optional, List, Dict, Any

from .connection import get_pool

__all__ = [
    "get_session",
    "upsert_session",
    "drop_session",
]

_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS calc_sessions (
    user_id   BIGINT PRIMARY KEY,
    step      SMALLINT NOT NULL DEFAULT 1,
    category  TEXT,
    template  TEXT,
    modules   TEXT[] DEFAULT '{}',
    support   TEXT
);
"""


async def _ensure_table() -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(_TABLE_SQL)


async def get_session(user_id: int) -> Optional[Dict[str, Any]]:
    await _ensure_table()
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM calc_sessions WHERE user_id=$1", user_id)
        return dict(row) if row else None


async def upsert_session(user_id: int, **fields) -> None:
    await _ensure_table()
    pool = await get_pool()
    columns = ["step", "category", "template", "modules", "support"]
    values = [fields.get(col) for col in columns]
    # build query dynamically
    set_parts = [f"{col} = EXCLUDED.{col}" for col in columns if fields.get(col) is not None]
    async with pool.acquire() as conn:
        await conn.execute(
            f"""
            INSERT INTO calc_sessions(user_id, {', '.join(col for col in columns)})
            VALUES($1, $2, $3, $4, $5, $6)
            ON CONFLICT (user_id) DO UPDATE SET {', '.join(set_parts)}
            """,
            user_id,
            *values,
        )


async def drop_session(user_id: int) -> None:
    await _ensure_table()
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM calc_sessions WHERE user_id=$1", user_id) 