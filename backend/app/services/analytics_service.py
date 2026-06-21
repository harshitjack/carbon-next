"""
PostgreSQL analytics logging service.

Replaces the former google-cloud-bigquery service.

Logs anonymised carbon events for aggregate analytics into Supabase
PostgreSQL tables. Privacy by design: device_id is NEVER logged —
only aggregate stats.

All writes are fire-and-forget: failures are logged as warnings
and never propagate to the caller.

Identical external contract to the previous bigquery_service:
  log_event_async(total_kg, diet_type, insight_source, top_category) → None
"""

from __future__ import annotations

import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Analytics tables (see migrations/002_analytics_schema.sql):
#   analytics_events  — raw event log (replaces BigQuery carbon_analytics.carbon_events)
#   recommendation_logs — per-insight logging for analytics
# ---------------------------------------------------------------------------


async def log_event_async(
    total_kg: float,
    diet_type: str,
    insight_source: str,
    top_category: str,
) -> None:
    """
    Asynchronously log a carbon calculation event to the analytics_events table.

    Runs fully async using the asyncpg driver.
    This function NEVER raises — all exceptions are caught and logged.

    Args:
        total_kg: User's total annual footprint in kg CO2e.
        diet_type: User's dietary pattern string.
        insight_source: "openrouter" or "rules".
        top_category: Highest-emission category name.
    """
    settings = get_settings()

    if not settings.SUPABASE_DB_URL:
        logger.debug("Analytics: SUPABASE_DB_URL not set — skipping event log")
        return

    try:
        # Import here to allow the service to be imported even when asyncpg
        # pool is not yet initialised
        from app.services.supabase_service import _get_pool

        pool = await _get_pool(settings.SUPABASE_DB_URL)

        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO analytics_events
                  (total_kg, diet_type, insight_source, top_category)
                VALUES ($1, $2, $3, $4)
                """,
                total_kg,
                diet_type,
                insight_source,
                top_category,
            )

        logger.debug(
            "Analytics event logged: total_kg=%.1f diet=%s source=%s top=%s",
            total_kg,
            diet_type,
            insight_source,
            top_category,
        )

    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Analytics logging failed (non-critical): %s — %s",
            type(exc).__name__,
            exc,
        )


async def log_recommendation(
    insight_source: str,
    category: str,
    estimated_saving_kg: float,
    priority: int,
) -> None:
    """
    Log a single recommendation into recommendation_logs.

    This function NEVER raises — all exceptions are caught and logged.

    Args:
        insight_source: "openrouter" or "rules".
        category: Emission category targeted.
        estimated_saving_kg: Estimated annual saving in kg CO2e.
        priority: Insight priority (1–3).
    """
    settings = get_settings()

    if not settings.SUPABASE_DB_URL:
        logger.debug("Analytics: SUPABASE_DB_URL not set — skipping recommendation log")
        return

    try:
        from app.services.supabase_service import _get_pool

        pool = await _get_pool(settings.SUPABASE_DB_URL)

        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO recommendation_logs
                  (insight_source, category, estimated_saving_kg, priority)
                VALUES ($1, $2, $3, $4)
                """,
                insight_source,
                category,
                estimated_saving_kg,
                priority,
            )

    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Recommendation log failed (non-critical): %s — %s",
            type(exc).__name__,
            exc,
        )


# ---------------------------------------------------------------------------
# Equivalent analytics queries (replaces BigQuery SQL equivalents)
# ---------------------------------------------------------------------------


async def query_top_categories(limit: int = 10) -> list[dict]:
    """
    Return the most common top-emission categories across all events.

    Equivalent BigQuery query:
      SELECT top_category, COUNT(*) as count
      FROM carbon_analytics.carbon_events
      GROUP BY top_category ORDER BY count DESC LIMIT 10
    """
    settings = get_settings()
    if not settings.SUPABASE_DB_URL:
        return []

    try:
        from app.services.supabase_service import _get_pool

        pool = await _get_pool(settings.SUPABASE_DB_URL)
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT top_category, COUNT(*) AS count
                FROM   analytics_events
                GROUP  BY top_category
                ORDER  BY count DESC
                LIMIT  $1
                """,
                limit,
            )
        return [dict(r) for r in rows]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Analytics query failed: %s — %s", type(exc).__name__, exc)
        return []


async def query_avg_footprint_by_diet() -> list[dict]:
    """
    Return average footprint per diet type across all logged events.

    Equivalent BigQuery query:
      SELECT diet_type, AVG(total_kg) as avg_kg, COUNT(*) as count
      FROM carbon_analytics.carbon_events
      GROUP BY diet_type
    """
    settings = get_settings()
    if not settings.SUPABASE_DB_URL:
        return []

    try:
        from app.services.supabase_service import _get_pool

        pool = await _get_pool(settings.SUPABASE_DB_URL)
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT diet_type,
                       ROUND(AVG(total_kg)::numeric, 1) AS avg_kg,
                       COUNT(*) AS count
                FROM   analytics_events
                GROUP  BY diet_type
                ORDER  BY avg_kg DESC
                """
            )
        return [dict(r) for r in rows]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Analytics query failed: %s — %s", type(exc).__name__, exc)
        return []
