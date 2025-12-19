-- ============================================================================
-- RepliMap Backend - D1 Schema
-- Cloudflare Workers + D1 (SQLite)
-- ============================================================================

-- Users table (linked to Stripe customers)
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    stripe_customer_id TEXT UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_stripe ON users(stripe_customer_id);

-- Licenses table
CREATE TABLE IF NOT EXISTS licenses (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    license_key TEXT UNIQUE NOT NULL,
    plan TEXT NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'solo', 'pro', 'team')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'canceled', 'expired', 'past_due')),
    stripe_subscription_id TEXT UNIQUE,
    stripe_price_id TEXT,
    current_period_start TEXT,
    current_period_end TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_licenses_key ON licenses(license_key);
CREATE INDEX IF NOT EXISTS idx_licenses_user ON licenses(user_id);
CREATE INDEX IF NOT EXISTS idx_licenses_stripe_sub ON licenses(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_licenses_status ON licenses(status);

-- Machine bindings
CREATE TABLE IF NOT EXISTS license_machines (
    id TEXT PRIMARY KEY,
    license_id TEXT NOT NULL REFERENCES licenses(id) ON DELETE CASCADE,
    machine_id TEXT NOT NULL,
    machine_name TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(license_id, machine_id)
);

CREATE INDEX IF NOT EXISTS idx_machines_license ON license_machines(license_id);
CREATE INDEX IF NOT EXISTS idx_machines_active ON license_machines(license_id, is_active);

-- Machine change tracking (for monthly limit of 3 changes)
CREATE TABLE IF NOT EXISTS machine_changes (
    id TEXT PRIMARY KEY,
    license_id TEXT NOT NULL REFERENCES licenses(id) ON DELETE CASCADE,
    old_machine_id TEXT,
    new_machine_id TEXT NOT NULL,
    changed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_changes_license ON machine_changes(license_id);
CREATE INDEX IF NOT EXISTS idx_changes_date ON machine_changes(changed_at);
CREATE INDEX IF NOT EXISTS idx_changes_license_date ON machine_changes(license_id, changed_at);

-- Usage logs for analytics
CREATE TABLE IF NOT EXISTS usage_logs (
    id TEXT PRIMARY KEY,
    license_id TEXT NOT NULL REFERENCES licenses(id) ON DELETE CASCADE,
    machine_id TEXT,
    action TEXT NOT NULL CHECK (action IN ('validate', 'activate', 'deactivate', 'scan')),
    resources_count INTEGER DEFAULT 0,
    metadata TEXT,  -- JSON string
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_usage_license ON usage_logs(license_id);
CREATE INDEX IF NOT EXISTS idx_usage_date ON usage_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_usage_action ON usage_logs(license_id, action, created_at);

-- Processed webhook events (for idempotency)
CREATE TABLE IF NOT EXISTS processed_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    processed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- AWS account tracking per license
CREATE TABLE IF NOT EXISTS license_aws_accounts (
    id TEXT PRIMARY KEY,
    license_id TEXT NOT NULL REFERENCES licenses(id) ON DELETE CASCADE,
    aws_account_id TEXT NOT NULL,
    account_alias TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(license_id, aws_account_id)
);

CREATE INDEX IF NOT EXISTS idx_aws_accounts_license ON license_aws_accounts(license_id);
CREATE INDEX IF NOT EXISTS idx_aws_accounts_active ON license_aws_accounts(license_id, is_active);

-- ============================================================================
-- Helper Views
-- ============================================================================

-- View for license with machine count
CREATE VIEW IF NOT EXISTS license_machine_counts AS
SELECT
    l.id as license_id,
    l.license_key,
    l.plan,
    l.status,
    COUNT(CASE WHEN lm.is_active = 1 THEN 1 END) as active_machines
FROM licenses l
LEFT JOIN license_machines lm ON l.id = lm.license_id
GROUP BY l.id;

-- View for monthly machine changes count
CREATE VIEW IF NOT EXISTS monthly_machine_changes AS
SELECT
    license_id,
    strftime('%Y-%m', changed_at) as month,
    COUNT(*) as change_count
FROM machine_changes
WHERE changed_at >= datetime('now', 'start of month')
GROUP BY license_id, strftime('%Y-%m', changed_at);

-- ============================================================================
-- Cleanup: Remove old processed events (run via scheduled worker)
-- DELETE FROM processed_events WHERE processed_at < datetime('now', '-30 days');
-- ============================================================================
