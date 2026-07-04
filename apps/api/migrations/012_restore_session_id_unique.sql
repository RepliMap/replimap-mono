-- Migration 012: Restore UNIQUE constraint on licenses.stripe_session_id
--
-- Context: migration 008 created `licenses_session_id_idx` as a UNIQUE index
-- for lifetime-purchase idempotency. Migration 011 rebuilt the licenses table
-- (licenses_new → RENAME), which dropped all indexes of the old table, and
-- recreated stripe_session_id's index as a plain (non-unique) index named
-- payment_session_id_idx.
--
-- Consequence: the race fallback in createLifetimeLicense (stripe-webhook.ts)
-- relies on UNIQUE(stripe_session_id) to reject a concurrent duplicate insert
-- for the same checkout session. Without the constraint, concurrent webhook
-- redeliveries can issue two licenses for one payment. The Drizzle schema
-- (src/db/schema.ts) already declares .unique() — this migration brings the
-- database back in line with it.
--
-- Safe to run everywhere: all licenses tables are currently empty of
-- duplicate session ids (prod has zero rows), and a UNIQUE index on a
-- nullable column allows any number of NULLs in SQLite.

DROP INDEX IF EXISTS payment_session_id_idx;
CREATE UNIQUE INDEX IF NOT EXISTS licenses_session_id_unique_idx
    ON licenses(stripe_session_id);
