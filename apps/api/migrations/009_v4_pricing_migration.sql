-- Migration: v4.0 Pricing Plan Names
-- Date: 2026-01-16
-- Description: Updates existing plan names to v4.0 naming convention
--
-- Mapping:
--   free -> community
--   solo -> pro (merged with existing pro)
--   enterprise -> sovereign
--
-- Note: This is a data migration, not schema migration.
-- The code handles legacy names at runtime via normalizePlanName(),
-- but this ensures data consistency.

-- Update free -> community
UPDATE licenses SET plan = 'community' WHERE plan = 'free';

-- Update solo -> pro
UPDATE licenses SET plan = 'pro' WHERE plan = 'solo';

-- Update enterprise -> sovereign
UPDATE licenses SET plan = 'sovereign' WHERE plan = 'enterprise';

-- Verify counts (for manual inspection)
-- SELECT plan, COUNT(*) FROM licenses GROUP BY plan;
