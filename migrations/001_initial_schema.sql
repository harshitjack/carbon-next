-- =============================================================================
-- Migration 001: Initial Schema
-- Replaces: Firestore "carbon_entries" collection
-- Run this in your Supabase SQL Editor or via psql before starting the app.
-- =============================================================================

-- Enable pgcrypto for gen_random_uuid() if not already enabled
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- -----------------------------------------------------------------------------
-- carbon_entries
-- Stores every carbon footprint calculation result, keyed by anonymous device_id.
-- Replaces Firestore collection "carbon_entries".
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carbon_entries (
    id                    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id             TEXT        NOT NULL,
    timestamp             TIMESTAMPTZ NOT NULL DEFAULT now(),
    total_kg              FLOAT       NOT NULL CHECK (total_kg >= 0),
    breakdown             JSONB       NOT NULL DEFAULT '{}',
    ranked_categories     JSONB       NOT NULL DEFAULT '[]',
    vs_global_average_pct FLOAT       NOT NULL DEFAULT 0,
    vs_paris_target_pct   FLOAT       NOT NULL DEFAULT 0,
    insights              JSONB       NOT NULL DEFAULT '[]'
);

-- Index for the primary query pattern: latest entries per device
CREATE INDEX IF NOT EXISTS carbon_entries_device_id_timestamp
    ON carbon_entries (device_id, timestamp DESC);

-- Row-level security (optional, enable if using Supabase RLS)
-- ALTER TABLE carbon_entries ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE  carbon_entries IS 'Carbon footprint calculation history per anonymous device.';
COMMENT ON COLUMN carbon_entries.id IS 'Globally unique entry ID (UUID v4).';
COMMENT ON COLUMN carbon_entries.device_id IS 'Opaque anonymous device identifier (no PII).';
COMMENT ON COLUMN carbon_entries.timestamp IS 'UTC timestamp of when the calculation was saved.';
COMMENT ON COLUMN carbon_entries.total_kg IS 'Total annual carbon footprint in kg CO2e.';
COMMENT ON COLUMN carbon_entries.breakdown IS 'JSONB map: {transport, home, diet, consumption} in kg CO2e.';
COMMENT ON COLUMN carbon_entries.ranked_categories IS 'JSONB array of {category, kg, percentage} sorted by kg desc.';
COMMENT ON COLUMN carbon_entries.vs_global_average_pct IS 'Footprint as % of global average (4000 kg CO2e).';
COMMENT ON COLUMN carbon_entries.vs_paris_target_pct IS 'Footprint as % of Paris 1.5°C target (2000 kg CO2e).';
COMMENT ON COLUMN carbon_entries.insights IS 'JSONB array of AI/rule-engine insight objects.';
