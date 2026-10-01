-- Migration: Add Lifetime Plan Support
-- Date: 2026-01-07
-- Description: Adds fields to support one-time lifetime purchases alongside subscriptions
--
-- Changes:
-- 1. Add plan_type column to distinguish between 'free', 'monthly', 'annual', 'lifetime'
-- 2. Add stripe_session_id column for lifetime purchase idempotency
-- 3. Add canceled_at, revoked_at, revoked_reason for status tracking
-- 4. Add indexes for new columns

-- Add plan_type column (default to 'monthly' for existing subscriptions)
ALTER TABLE licenses ADD COLUMN plan_type TEXT NOT NULL DEFAULT 'monthly';

-- Add stripe_session_id column (for lifetime idempotency)
ALTER TABLE licenses ADD COLUMN stripe_session_id TEXT;

-- Add status tracking columns
ALTER TABLE licenses ADD COLUMN canceled_at TEXT;
ALTER TABLE licenses ADD COLUMN revoked_at TEXT;
ALTER TABLE licenses ADD COLUMN revoked_reason TEXT;

-- Create indexes for new columns
CREATE INDEX IF NOT EXISTS licenses_plan_type_idx ON licenses(plan_type);
CREATE UNIQUE INDEX IF NOT EXISTS licenses_session_id_idx ON licenses(stripe_session_id);
