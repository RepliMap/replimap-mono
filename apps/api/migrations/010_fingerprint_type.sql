-- ============================================================================
-- Migration: Add fingerprint type support to license_machines
-- ============================================================================

-- Add fingerprint_type column with default 'machine'
ALTER TABLE license_machines ADD COLUMN fingerprint_type TEXT DEFAULT 'machine';

-- Add CI metadata columns
ALTER TABLE license_machines ADD COLUMN ci_provider TEXT;
ALTER TABLE license_machines ADD COLUMN ci_repo TEXT;

-- Add container metadata
ALTER TABLE license_machines ADD COLUMN container_type TEXT;

-- Create index for CI lookups
CREATE INDEX IF NOT EXISTS idx_license_machines_ci
ON license_machines(license_id, ci_provider, ci_repo)
WHERE ci_provider IS NOT NULL;

-- Create index for fingerprint type queries
CREATE INDEX IF NOT EXISTS idx_license_machines_fp_type
ON license_machines(license_id, fingerprint_type);
