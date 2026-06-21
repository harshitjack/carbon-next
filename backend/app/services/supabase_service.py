"""
Supabase PostgreSQL persistence service for carbon footprint entries.

Replaces the former google-cloud-firestore service.

Provides async operations backed by asyncpg connection pooling, plus the
original in-memory fallback store used when USE_SUPABASE=false (local dev).

Identical external contract to the previous firestore_service:
  save_entry(device_id, result, insights) → str
  get_history(device_id, limit) → list[dict]
  save_entry_memory(device_id, result, insights) → str   (fallback)
  get_history_memory(device_id, limit) → list[dict]       (fallback)
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

import asyncpg

from app.models.carbon import CarbonResult
from app.models.insights import InsightItem

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory fallback store (keyed by device_id, list of entries)
# Preserves original firestore_service._memory_store interface for tests.
# ---------------------------------------------------------------------------
_memory_store: dict[str, list[dict[str, Any]]] = {}

# ---------------------------------------------------------------------------
# Connection pool — created on first use, re-used across requests
# ---------------------------------------------------------------------------
_pool: asyncpg.Pool | None = None
_pool_lock = asyncio.Lock()


async def _get_pool(db_url: str) -> asyncpg.Pool:
    """Return the shared asyncpg connection pool, creating it if necessary."""
    global _pool
    if _pool is not None:
        return _pool

    async with _pool_lock:
        # Double-check after acquiring lock
        if _pool is None:
            _pool = await asyncpg.create_pool(
                dsn=db_url,
                min_size=1,
                max_size=10,
                command_timeout=10,
                # asyncpg requires a codec for JSONB columns
                init=_init_connection,
            )
    return _pool  # type: ignore[return-value]


async def _init_connection(conn: asyncpg.Connection) -> None:
    """Register JSON codec so JSONB columns are automatically serialised/deserialised."""
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )
    await conn.set_type_codec(
        "json",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


# ---------------------------------------------------------------------------
# Supabase (PostgreSQL) implementations
# ---------------------------------------------------------------------------


async def save_entry(
    device_id: str,
    result: CarbonResult,
    insights: list[InsightItem],
    *,
    db_url: str,
) -> str:
    """
    Persist a carbon entry to Supabase PostgreSQL.

    Args:
        device_id: Anonymous device identifier.
        result: Calculated carbon result.
        insights: Generated insights.
        db_url: PostgreSQL connection string.

    Returns:
        UUID string of the inserted row.
    """
    pool = await _get_pool(db_url)

    insights_json = [insight.model_dump() for insight in insights]
    ranked_json = [rc.model_dump() for rc in result.ranked_categories]

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO carbon_entries
              (device_id, total_kg, breakdown, ranked_categories,
               vs_global_average_pct, vs_paris_target_pct, insights)
            VALUES ($1, $2, $3::jsonb, $4::jsonb, $5, $6, $7::jsonb)
            RETURNING id::text
            """,
            device_id,
            result.total_kg,
            result.breakdown,
            ranked_json,
            result.vs_global_average_pct,
            result.vs_paris_target_pct,
            insights_json,
        )

    doc_id: str = row["id"]
    logger.info("Saved Supabase entry %s for device %s", doc_id, device_id[:8])
    return doc_id


async def get_history(
    device_id: str,
    limit: int = 20,
    *,
    db_url: str,
) -> list[dict[str, Any]]:
    """
    Retrieve carbon history entries for a device from Supabase.

    Args:
        device_id: Anonymous device identifier.
        limit: Maximum number of entries to return.
        db_url: PostgreSQL connection string.

    Returns:
        List of entry dicts ordered newest first.
    """
    pool = await _get_pool(db_url)

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id::text,
                   device_id,
                   timestamp AT TIME ZONE 'UTC' AS timestamp,
                   total_kg,
                   breakdown,
                   ranked_categories,
                   vs_global_average_pct,
                   vs_paris_target_pct,
                   insights
            FROM   carbon_entries
            WHERE  device_id = $1
            ORDER  BY timestamp DESC
            LIMIT  $2
            """,
            device_id,
            limit,
        )

    entries: list[dict[str, Any]] = []
    for row in rows:
        entry = dict(row)
        # Convert datetime to ISO string for JSON serialisation
        if hasattr(entry.get("timestamp"), "isoformat"):
            entry["timestamp"] = entry["timestamp"].isoformat()
        entries.append(entry)

    return entries


# ---------------------------------------------------------------------------
# In-memory fallback implementations (USE_SUPABASE=false)
# Identical to the original firestore_service memory implementations.
# ---------------------------------------------------------------------------


async def save_entry_memory(
    device_id: str,
    result: CarbonResult,
    insights: list[InsightItem],
) -> str:
    """
    Save a carbon footprint entry to the local in-memory store.

    Args:
        device_id: Anonymous device identifier.
        result: Calculated carbon footprint result.
        insights: Generated reduction insights.

    Returns:
        Generated memory document ID string.
    """
    doc_id = str(uuid.uuid4())
    entry: dict[str, Any] = {
        "id": doc_id,
        "device_id": device_id,
        "timestamp": datetime.now(tz=UTC).isoformat(),
        "total_kg": result.total_kg,
        "breakdown": result.breakdown,
        "ranked_categories": [rc.model_dump() for rc in result.ranked_categories],
        "vs_global_average_pct": result.vs_global_average_pct,
        "vs_paris_target_pct": result.vs_paris_target_pct,
        "insights": [insight.model_dump() for insight in insights],
    }
    if device_id not in _memory_store:
        _memory_store[device_id] = []
    _memory_store[device_id].insert(0, entry)  # newest first
    logger.debug("Saved in-memory entry %s for device %s", doc_id, device_id[:8])
    return doc_id


async def get_history_memory(device_id: str, limit: int = 20) -> list[dict[str, Any]]:
    """
    Retrieve carbon calculation history for a device from memory.

    Args:
        device_id: Anonymous device identifier.
        limit: Maximum number of entries to return.

    Returns:
        List of historical entry dicts.
    """
    entries = _memory_store.get(device_id, [])
    return entries[:limit]
