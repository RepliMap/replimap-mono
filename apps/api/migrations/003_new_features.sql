-- ============================================================================
-- Migration: Add new feature tracking tables
-- Version: 003_new_features.sql
-- ============================================================================

-- Usage events table for detailed feature tracking
CREATE TABLE IF NOT EXISTS usage_events (
    id TEXT PRIMARY KEY,
    license_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    region TEXT,
    vpc_id TEXT,
    resource_count INTEGER DEFAULT 0,
    duration_ms INTEGER,
    metadata TEXT,
    original_event_type TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (license_id) REFERENCES licenses(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_usage_events_license ON usage_events(license_id);
CREATE INDEX IF NOT EXISTS idx_usage_events_type ON usage_events(event_type);
CREATE INDEX IF NOT EXISTS idx_usage_events_date ON usage_events(created_at);
CREATE INDEX IF NOT EXISTS idx_usage_events_license_type ON usage_events(license_id, event_type);

-- Snapshot storage table
CREATE TABLE IF NOT EXISTS snapshots (
    id TEXT PRIMARY KEY,
    license_id TEXT NOT NULL,
    name TEXT NOT NULL,
    region TEXT NOT NULL,
    vpc_id TEXT,
    resource_count INTEGER DEFAULT 0,
    profile TEXT,
    replimap_version TEXT,
    storage_type TEXT DEFAULT 'local',
    storage_path TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (license_id) REFERENCES licenses(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_snapshots_license ON snapshots(license_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_name ON snapshots(license_id, name);
CREATE INDEX IF NOT EXISTS idx_snapshots_created ON snapshots(created_at);

-- Remediation tracking table
CREATE TABLE IF NOT EXISTS remediations (
    id TEXT PRIMARY KEY,
    license_id TEXT NOT NULL,
    audit_id TEXT,
    region TEXT NOT NULL,
    total_findings INTEGER DEFAULT 0,
    total_fixable INTEGER DEFAULT 0,
    total_manual INTEGER DEFAULT 0,
    files_generated INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (license_id) REFERENCES licenses(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_remediations_license ON remediations(license_id);
CREATE INDEX IF NOT EXISTS idx_remediations_created ON remediations(created_at);

-- Migrations log table
CREATE TABLE IF NOT EXISTS migrations_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration_name TEXT NOT NULL UNIQUE,
    executed_at TEXT NOT NULL DEFAULT (datetime('now')),
    notes TEXT
);

-- Log this migration
INSERT OR IGNORE INTO migrations_log (migration_name, notes)
VALUES ('003_new_features', 'Added usage_events, snapshots, remediations tables');
