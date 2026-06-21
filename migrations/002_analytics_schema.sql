-- =============================================================================
-- Migration 002: Analytics Schema
-- Replaces: BigQuery dataset "carbon_analytics" with tables:
--   analytics_events    (was: BigQuery carbon_analytics.carbon_events)
--   user_metrics        (new: aggregated per-device stats)
--   recommendation_logs (new: per-insight logging)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- analytics_events
-- Anonymised event log for aggregate analytics.
-- Replaces BigQuery table: carbon_analytics.carbon_events
-- Schema intentionally mirrors the original BigQuery table columns.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analytics_events (
    id             BIGSERIAL   PRIMARY KEY,
    timestamp      TIMESTAMPTZ NOT NULL DEFAULT now(),
    total_kg       FLOAT       NOT NULL CHECK (total_kg >= 0),
    diet_type      TEXT        NOT NULL,
    insight_source TEXT        NOT NULL,   -- 'openrouter' | 'rules'
    top_category   TEXT        NOT NULL    -- 'transport' | 'home' | 'diet' | 'consumption'
);

-- Time-based queries and diet/category analytics
CREATE INDEX IF NOT EXISTS analytics_events_timestamp
    ON analytics_events (timestamp DESC);

CREATE INDEX IF NOT EXISTS analytics_events_diet_type
    ON analytics_events (diet_type);

CREATE INDEX IF NOT EXISTS analytics_events_top_category
    ON analytics_events (top_category);

COMMENT ON TABLE  analytics_events IS 'Anonymised carbon calculation events for aggregate analytics. No device_id stored.';
COMMENT ON COLUMN analytics_events.total_kg IS 'Total annual footprint in kg CO2e.';
COMMENT ON COLUMN analytics_events.diet_type IS 'Dietary pattern: meat_heavy | meat_medium | vegetarian | vegan.';
COMMENT ON COLUMN analytics_events.insight_source IS 'AI engine used: openrouter | rules.';
COMMENT ON COLUMN analytics_events.top_category IS 'Highest emission category for this user.';

-- -----------------------------------------------------------------------------
-- user_metrics
-- Aggregated per-device lifetime stats (updated on each calculation).
-- New table — no BigQuery equivalent.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_metrics (
    device_id          TEXT        PRIMARY KEY,
    first_seen         TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen          TIMESTAMPTZ NOT NULL DEFAULT now(),
    total_calculations INT         NOT NULL DEFAULT 0 CHECK (total_calculations >= 0),
    avg_footprint_kg   FLOAT       NOT NULL DEFAULT 0 CHECK (avg_footprint_kg >= 0)
);

COMMENT ON TABLE  user_metrics IS 'Aggregated lifetime stats per anonymous device.';
COMMENT ON COLUMN user_metrics.device_id IS 'Opaque anonymous device identifier (no PII).';
COMMENT ON COLUMN user_metrics.total_calculations IS 'Total number of footprint calculations performed.';
COMMENT ON COLUMN user_metrics.avg_footprint_kg IS 'Rolling average annual footprint in kg CO2e.';

-- -----------------------------------------------------------------------------
-- recommendation_logs
-- Per-insight logging for effectiveness tracking.
-- New table — no BigQuery equivalent.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS recommendation_logs (
    id                  BIGSERIAL   PRIMARY KEY,
    timestamp           TIMESTAMPTZ NOT NULL DEFAULT now(),
    insight_source      TEXT        NOT NULL,   -- 'openrouter' | 'rules'
    category            TEXT        NOT NULL,
    estimated_saving_kg FLOAT       NOT NULL CHECK (estimated_saving_kg >= 0),
    priority            INT         NOT NULL CHECK (priority BETWEEN 1 AND 3)
);

CREATE INDEX IF NOT EXISTS recommendation_logs_source
    ON recommendation_logs (insight_source);

CREATE INDEX IF NOT EXISTS recommendation_logs_category
    ON recommendation_logs (category);

COMMENT ON TABLE  recommendation_logs IS 'Per-insight recommendation log for effectiveness tracking.';
COMMENT ON COLUMN recommendation_logs.insight_source IS 'Engine that generated this insight: openrouter | rules.';
COMMENT ON COLUMN recommendation_logs.category IS 'Emission category targeted by the insight.';
COMMENT ON COLUMN recommendation_logs.estimated_saving_kg IS 'Estimated annual CO2e saving in kg if action is taken.';
COMMENT ON COLUMN recommendation_logs.priority IS 'Priority ranking 1 (highest) to 3 (lowest).';

-- -----------------------------------------------------------------------------
-- Equivalent analytics views (replaces BigQuery SQL queries)
-- -----------------------------------------------------------------------------

-- View: top categories by frequency
CREATE OR REPLACE VIEW v_top_categories AS
SELECT   top_category,
         COUNT(*) AS event_count,
         ROUND(AVG(total_kg)::numeric, 1) AS avg_total_kg
FROM     analytics_events
GROUP BY top_category
ORDER BY event_count DESC;

-- View: footprint by diet type
CREATE OR REPLACE VIEW v_footprint_by_diet AS
SELECT   diet_type,
         COUNT(*) AS count,
         ROUND(AVG(total_kg)::numeric, 1) AS avg_kg,
         ROUND(MIN(total_kg)::numeric, 1) AS min_kg,
         ROUND(MAX(total_kg)::numeric, 1) AS max_kg
FROM     analytics_events
GROUP BY diet_type
ORDER BY avg_kg DESC;

-- View: AI vs rule engine usage
CREATE OR REPLACE VIEW v_insight_source_stats AS
SELECT   insight_source,
         COUNT(*) AS count,
         ROUND(100.0 * COUNT(*) / NULLIF(SUM(COUNT(*)) OVER (), 0), 1) AS pct
FROM     analytics_events
GROUP BY insight_source;
