-- ============================================================================
-- Migration: Rename blast → deps
-- Version: 004_blast_to_deps_rename.sql
--
-- This migration:
-- 1. Renames existing 'blast' events to 'deps'
-- 2. Creates backward compatibility index
-- 3. Updates any stored references
-- ============================================================================

-- Step 1: Rename existing events
UPDATE usage_events
SET event_type = 'deps',
    original_event_type = 'blast'
WHERE event_type = 'blast';

UPDATE usage_events
SET event_type = 'deps_export',
    original_event_type = 'blast_export'
WHERE event_type = 'blast_export';

UPDATE usage_events
SET event_type = 'deps_explore',
    original_event_type = 'blast_analyze'
WHERE event_type = 'blast_analyze';

-- Step 2: Create index for new event types
CREATE INDEX IF NOT EXISTS idx_usage_events_deps
ON usage_events(license_id, event_type)
WHERE event_type IN ('deps', 'deps_export', 'deps_explore');

-- Step 3: Log the migration
INSERT OR IGNORE INTO migrations_log (migration_name, notes)
VALUES (
    '004_blast_to_deps_rename',
    'Renamed blast/blast_export/blast_analyze to deps/deps_export/deps_explore for legal compliance'
);
