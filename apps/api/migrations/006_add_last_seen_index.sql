-- ============================================================================
-- Migration: Add last_seen_at index for efficient device queries
-- Version: 006_add_last_seen_index.sql
--
-- This index optimizes queries that filter by last_seen_at, such as:
-- - Finding devices active in the last 7/30 days
-- - Admin stats endpoint device counts
-- - Scheduled cleanup of stale devices
-- ============================================================================

-- Add composite index for efficient last_seen queries
CREATE INDEX IF NOT EXISTS idx_machines_last_seen
ON license_machines(license_id, last_seen_at);

-- Log the migration
INSERT OR IGNORE INTO migrations_log (migration_name, notes)
VALUES (
    '006_add_last_seen_index',
    'Added index on license_machines(license_id, last_seen_at) for efficient device activity queries'
);
