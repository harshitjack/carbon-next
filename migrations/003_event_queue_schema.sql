-- =============================================================================
-- Migration 003: Event Queue Schema
-- Replaces: Google Cloud Pub/Sub topic "carbon-insights"
-- Implements a durable, database-backed event queue with at-least-once
-- delivery semantics using PostgreSQL advisory locks / SKIP LOCKED.
-- =============================================================================

-- Event status enum
DO $$ BEGIN
    CREATE TYPE event_status AS ENUM ('pending', 'processing', 'done', 'failed');
EXCEPTION
    WHEN duplicate_object THEN NULL;  -- idempotent: type already exists
END $$;

-- -----------------------------------------------------------------------------
-- event_queue
-- Durable FIFO queue for asynchronous events published by the application.
-- Replaces Google Cloud Pub/Sub topic: carbon-insights
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS event_queue (
    id           BIGSERIAL    PRIMARY KEY,
    event_type   TEXT         NOT NULL,      -- e.g. 'insight_request'
    payload      JSONB        NOT NULL,      -- event data (no PII)
    status       event_status NOT NULL DEFAULT 'pending',
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    processed_at TIMESTAMPTZ  NULL,
    retry_count  INT          NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
    error_msg    TEXT         NULL           -- last error message if failed
);

-- Primary consumption index: pending events in order (SKIP LOCKED compatible)
CREATE INDEX IF NOT EXISTS event_queue_status_created
    ON event_queue (status, created_at)
    WHERE status = 'pending';

-- Index for monitoring: view all events by type
CREATE INDEX IF NOT EXISTS event_queue_event_type
    ON event_queue (event_type);

-- Index for housekeeping: find old done/failed events
CREATE INDEX IF NOT EXISTS event_queue_processed_at
    ON event_queue (processed_at)
    WHERE processed_at IS NOT NULL;

COMMENT ON TABLE  event_queue IS 'Database-backed async event queue. Replaces Google Pub/Sub.';
COMMENT ON COLUMN event_queue.event_type IS 'Event type identifier, e.g. insight_request.';
COMMENT ON COLUMN event_queue.payload IS 'JSONB event payload — must contain no PII.';
COMMENT ON COLUMN event_queue.status IS 'Lifecycle: pending → processing → done | failed.';
COMMENT ON COLUMN event_queue.retry_count IS 'Number of processing attempts made.';
COMMENT ON COLUMN event_queue.error_msg IS 'Last error message when status = failed.';

-- -----------------------------------------------------------------------------
-- Housekeeping: auto-delete completed events older than 30 days
-- (run this periodically via pg_cron or a scheduled job)
-- -----------------------------------------------------------------------------
-- DELETE FROM event_queue
-- WHERE  status IN ('done', 'failed')
--   AND  processed_at < now() - INTERVAL '30 days';

-- -----------------------------------------------------------------------------
-- Monitoring view: queue depth by status
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_event_queue_stats AS
SELECT   status,
         event_type,
         COUNT(*)                     AS count,
         MIN(created_at)              AS oldest,
         MAX(created_at)              AS newest,
         AVG(EXTRACT(EPOCH FROM (COALESCE(processed_at, now()) - created_at)))::INT AS avg_processing_secs
FROM     event_queue
GROUP BY status, event_type
ORDER BY status, event_type;
