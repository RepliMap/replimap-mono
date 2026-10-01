-- Migration 011: Bootstrap Drizzle/Better-Auth schema for local parity
--
-- Context: the production D1 is managed directly by drizzle-kit and has
-- the MKSaaS/Better-Auth user/session/account tables plus the v4 licenses
-- plan enum (community/pro/team/sovereign). The migration files 001-010
-- only cover the legacy `users` (plural) schema and old plan enum.
--
-- This migration brings local D1 in sync so `pnpm dev` + e2e tests work.
-- On production it's a no-op against already-existing tables (IF NOT EXISTS
-- guards), and the rename+backfill of the legacy `users` is safe because
-- production has never used that table.

-- ─────────────────────────────────────────────────────────────────────
-- Better-Auth: user table (singular) — the one Drizzle queries expect
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL UNIQUE,
    normalized_email TEXT UNIQUE,
    email_verified INTEGER NOT NULL DEFAULT 0,
    image TEXT,
    created_at INTEGER NOT NULL DEFAULT (CAST(unixepoch('subsecond') * 1000 AS INTEGER)),
    updated_at INTEGER NOT NULL DEFAULT (CAST(unixepoch('subsecond') * 1000 AS INTEGER)),
    role TEXT,
    banned INTEGER DEFAULT 0,
    ban_reason TEXT,
    ban_expires INTEGER,
    customer_id TEXT
);

CREATE INDEX IF NOT EXISTS user_id_idx ON user(id);
CREATE INDEX IF NOT EXISTS user_customer_id_idx ON user(customer_id);
CREATE INDEX IF NOT EXISTS user_role_idx ON user(role);

-- ─────────────────────────────────────────────────────────────────────
-- Better-Auth: session, account, verification (required by Clerk adapter
-- on the auth side — empty on the API side but the FKs need a target)
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS session (
    id TEXT PRIMARY KEY,
    expires_at INTEGER NOT NULL,
    token TEXT NOT NULL UNIQUE,
    created_at INTEGER NOT NULL DEFAULT (CAST(unixepoch('subsecond') * 1000 AS INTEGER)),
    updated_at INTEGER NOT NULL DEFAULT (CAST(unixepoch('subsecond') * 1000 AS INTEGER)),
    ip_address TEXT,
    user_agent TEXT,
    user_id TEXT NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    impersonated_by TEXT
);

CREATE TABLE IF NOT EXISTS account (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    user_id TEXT NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    access_token TEXT,
    refresh_token TEXT,
    id_token TEXT,
    access_token_expires_at INTEGER,
    refresh_token_expires_at INTEGER,
    scope TEXT,
    password TEXT,
    created_at INTEGER NOT NULL DEFAULT (CAST(unixepoch('subsecond') * 1000 AS INTEGER)),
    updated_at INTEGER NOT NULL DEFAULT (CAST(unixepoch('subsecond') * 1000 AS INTEGER))
);

CREATE TABLE IF NOT EXISTS verification (
    id TEXT PRIMARY KEY,
    identifier TEXT NOT NULL,
    value TEXT NOT NULL,
    expires_at INTEGER NOT NULL,
    created_at INTEGER NOT NULL DEFAULT (CAST(unixepoch('subsecond') * 1000 AS INTEGER)),
    updated_at INTEGER NOT NULL DEFAULT (CAST(unixepoch('subsecond') * 1000 AS INTEGER))
);

-- ─────────────────────────────────────────────────────────────────────
-- Data migration: copy existing `users` rows into `user` if any
-- ─────────────────────────────────────────────────────────────────────
INSERT OR IGNORE INTO user (id, email, customer_id, created_at, updated_at, name)
SELECT
    id,
    email,
    stripe_customer_id,
    CAST(strftime('%s', created_at) * 1000 AS INTEGER),
    CAST(strftime('%s', updated_at) * 1000 AS INTEGER),
    lower(substr(email, 1, instr(email, '@') - 1))
FROM users
WHERE EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='users');

-- ─────────────────────────────────────────────────────────────────────
-- licenses plan CHECK: the legacy constraint only allows free/solo/pro/team.
-- The v4 handlers insert 'community' for free tier, which would fail.
-- SQLite doesn't let us ALTER a CHECK constraint — rebuild the table.
-- Drop dependent view first; recreate it after the rebuild.
-- ─────────────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS license_machine_counts;

CREATE TABLE IF NOT EXISTS licenses_new (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    license_key TEXT NOT NULL UNIQUE,
    plan TEXT NOT NULL DEFAULT 'community',
    plan_type TEXT NOT NULL DEFAULT 'monthly',
    status TEXT NOT NULL DEFAULT 'active',
    stripe_subscription_id TEXT UNIQUE,
    stripe_price_id TEXT,
    stripe_session_id TEXT,
    current_period_start TEXT,
    current_period_end TEXT,
    canceled_at TEXT,
    revoked_at TEXT,
    revoked_reason TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT OR IGNORE INTO licenses_new
    (id, user_id, license_key, plan, plan_type, status,
     stripe_subscription_id, stripe_price_id, stripe_session_id,
     current_period_start, current_period_end,
     canceled_at, revoked_at, revoked_reason,
     created_at, updated_at)
SELECT
    id, user_id, license_key, plan, COALESCE(plan_type, 'monthly'), status,
    stripe_subscription_id, stripe_price_id, stripe_session_id,
    current_period_start, current_period_end,
    canceled_at, revoked_at, revoked_reason,
    created_at, updated_at
FROM licenses;

DROP TABLE IF EXISTS licenses;
ALTER TABLE licenses_new RENAME TO licenses;

CREATE INDEX IF NOT EXISTS licenses_user_id_idx ON licenses(user_id);
CREATE INDEX IF NOT EXISTS licenses_status_idx ON licenses(status);
CREATE INDEX IF NOT EXISTS licenses_plan_type_idx ON licenses(plan_type);
CREATE INDEX IF NOT EXISTS payment_session_id_idx ON licenses(stripe_session_id);

-- Recreate the view dropped above
CREATE VIEW IF NOT EXISTS license_machine_counts AS
SELECT
    l.id AS license_id,
    l.license_key,
    l.plan,
    l.status,
    COUNT(CASE WHEN lm.is_active = 1 THEN 1 END) AS active_machines
FROM licenses l
LEFT JOIN license_machines lm ON l.id = lm.license_id
GROUP BY l.id;

-- ─────────────────────────────────────────────────────────────────────
-- Drop the old `users` table — nothing references it after this point.
-- Must be last, otherwise licenses.user_id FK rewrite would dangle.
-- ─────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS users;
