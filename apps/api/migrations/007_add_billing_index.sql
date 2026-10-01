-- ============================================================================
-- Migration: Add billing composite index for efficient quota queries
-- Version: 007_add_billing_index.sql
--
-- This composite index optimizes the hybrid billing query that sums usage
-- from both usage_events (legacy) and usage_daily (new) tables.
--
-- Query pattern:
--   SELECT COUNT(*) FROM usage_events
--   WHERE license_id = ? AND event_type = ? AND created_at >= ?
-- ============================================================================

-- Composite index for billing queries (license_id, event_type, created_at)
-- This is more efficient than the existing idx_usage_events_license_type
-- because it includes created_at for date range filtering.
CREATE INDEX IF NOT EXISTS idx_usage_events_billing
ON usage_events(license_id, event_type, created_at);

-- Log the migration
INSERT OR IGNORE INTO migrations_log (migration_name, notes)
VALUES (
    '007_add_billing_index',
    'Added composite index for efficient billing/quota queries on usage_events'
);
