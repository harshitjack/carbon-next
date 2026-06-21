"""
Database-backed event queue service.

Replaces the former google-cloud-pubsub service.

Publishes lightweight events by inserting rows into the event_queue table
in Supabase PostgreSQL, enabling downstream processors to consume them.

All publishes are fire-and-forget: failures are logged as warnings
and never propagate to the caller.

Identical external contract to the previous pubsub_service:
  publish_insight_request(footprint_total, top_category) → None
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Event types
EVENT_INSIGHT_REQUEST = "insight_request"


async def publish_insight_request(
    footprint_total: float,
    top_category: str,
) -> None:
    """
    Asynchronously publish a carbon insight event to the event_queue table.

    Payload (no PII):
        footprint_total: Total annual kg CO2e
        top_category: Highest-emission category name
        timestamp: UTC ISO 8601 string

    This function NEVER raises — all exceptions are caught and logged.

    Args:
        footprint_total: User's total annual footprint in kg CO2e.
        top_category: Name of the user's highest-emission category.
    """
    settings = get_settings()

    if not settings.SUPABASE_DB_URL:
        logger.debug("EventQueue: SUPABASE_DB_URL not set — skipping event publish")
        return

    payload = {
        "footprint_total": footprint_total,
        "top_category": top_category,
        "timestamp": datetime.now(tz=UTC).isoformat(),
    }

    try:
        from app.services.supabase_service import _get_pool

        pool = await _get_pool(settings.SUPABASE_DB_URL)

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO event_queue (event_type, payload)
                VALUES ($1, $2::jsonb)
                RETURNING id
                """,
                EVENT_INSIGHT_REQUEST,
                json.dumps(payload),
            )

        logger.debug(
            "Event published to queue: id=%s type=%s top_category=%s",
            row["id"],
            EVENT_INSIGHT_REQUEST,
            top_category,
        )

    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Event queue publish failed (non-critical): %s — %s",
            type(exc).__name__,
            exc,
        )


async def process_pending_events(batch_size: int = 10) -> int:
    """
    Process a batch of pending events from the event_queue.

    Marks events as 'processing' before handling and 'done' or 'failed'
    afterwards to preserve at-least-once delivery semantics.

    This is a minimal processor implementation — extend as needed for
    more complex downstream handlers.

    Args:
        batch_size: Maximum number of events to process in one call.

    Returns:
        Number of events successfully processed.
    """
    settings = get_settings()

    if not settings.SUPABASE_DB_URL:
        return 0

    processed = 0

    try:
        from app.services.supabase_service import _get_pool

        pool = await _get_pool(settings.SUPABASE_DB_URL)

        async with pool.acquire() as conn:
            # Claim a batch atomically
            rows = await conn.fetch(
                """
                UPDATE event_queue
                SET    status = 'processing'
                WHERE  id IN (
                    SELECT id FROM event_queue
                    WHERE  status = 'pending'
                    ORDER  BY created_at
                    LIMIT  $1
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING id, event_type, payload
                """,
                batch_size,
            )

            for row in rows:
                try:
                    # Placeholder: route to appropriate handler by event_type
                    event_type = row["event_type"]
                    logger.debug("Processing event %s type=%s", row["id"], event_type)

                    # Mark done
                    await conn.execute(
                        """
                        UPDATE event_queue
                        SET status = 'done', processed_at = now()
                        WHERE id = $1
                        """,
                        row["id"],
                    )
                    processed += 1

                except Exception as inner_exc:  # noqa: BLE001
                    logger.warning(
                        "Event %s processing failed: %s — %s",
                        row["id"],
                        type(inner_exc).__name__,
                        inner_exc,
                    )
                    await conn.execute(
                        "UPDATE event_queue SET status = 'failed' WHERE id = $1",
                        row["id"],
                    )

    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Event queue processor error (non-critical): %s — %s",
            type(exc).__name__,
            exc,
        )

    return processed
