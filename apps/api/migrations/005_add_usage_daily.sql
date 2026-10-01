-- ============================================================================
-- Migration: Add usage_daily table for efficient telemetry aggregation
-- Version: 005_add_usage_daily.sql
--
-- This migration:
-- 1. Creates the usage_daily table for aggregated daily counts
-- 2. Creates indexes for efficient queries
-- 3. Reduces database bloat from 1.8M rows/year to ~50k rows/year
--
-- IMPORTANT: This table works alongside usage_events (hybrid read).
-- The getDailyUsageCount function sums from BOTH tables to ensure
-- no billing data is lost during the transition.
-- ============================================================================

-- Step 1: Create the usage_daily table
CREATE TABLE IF NOT EXISTS usage_daily (
    id TEXT PRIMARY KEY,
    license_id TEXT NOT NULL REFERENCES licenses(id) ON DELETE CASCADE,
    date TEXT NOT NULL,  -- YYYY-MM-DD format
    event_type TEXT NOT NULL,
    count INTEGER NOT NULL DEFAULT 1,
    resource_count INTEGER DEFAULT 0,  -- Sum of resources for this day
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(license_id, date, event_type)
);

-- Step 2: Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_usage_daily_license ON usage_daily(license_id);
CREATE INDEX IF NOT EXISTS idx_usage_daily_date ON usage_daily(date);
CREATE INDEX IF NOT EXISTS idx_usage_daily_lookup ON usage_daily(license_id, date, event_type);

-- Step 3: Log the migration
INSERT OR IGNORE INTO migrations_log (migration_name, notes)
VALUES (
    '005_add_usage_daily',
    'Added usage_daily table for efficient telemetry aggregation (upsert pattern instead of per-event inserts)'
);
