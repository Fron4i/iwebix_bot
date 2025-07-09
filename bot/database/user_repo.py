import asyncpg
from typing import Optional

from .connection import get_pool

__all__ = [
    "get_coupon",
    "set_coupon",
]

_TABLE_INITIALIZED = False

async def _ensure_table() -> None:
    global _TABLE_INITIALIZED
    if _TABLE_INITIALIZED:
        return
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bot_users (
                user_id BIGINT PRIMARY KEY,
                coupon_code TEXT
            );
            """
        )
    _TABLE_INITIALIZED = True

async def get_coupon(user_id: int) -> Optional[str]:
    await _ensure_table()
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT coupon_code FROM bot_users WHERE user_id=$1", user_id)
        return row["coupon_code"] if row and row["coupon_code"] else None

async def set_coupon(user_id: int, coupon_code: str) -> None:
    await _ensure_table()
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO bot_users(user_id, coupon_code) VALUES($1,$2) "
            "ON CONFLICT (user_id) DO UPDATE SET coupon_code = $2",
            user_id,
            coupon_code,
        ) 