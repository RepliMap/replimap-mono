/**
 * Admin-issued offline license blob (Sovereign, air-gapped hosts).
 *
 * POST /v1/admin/licenses/{key}/offline-blob
 * GET  /v1/admin/licenses/{key}/offline-blobs   (issuance ledger, no blobs)
 *
 * A blob cannot be revoked once issued, so the endpoint is deliberately
 * strict:
 *  - machine_id is REQUIRED (32 lowercase hex) — never emits an unbound blob.
 *  - expires_at is REQUIRED and is used verbatim as the signed `exp`. There is
 *    no fallback (no deriveLicenseExpiry / 365-day default / plan grace).
 *  - signing fails CLOSED (503) when LICENSE_SIGNING_KEY is not configured.
 *  - every issuance is written to a ledger BEFORE the blob is returned; if the
 *    ledger write fails the blob is not returned.
 *
 * Ledger storage (no schema migration): a `usage_logs` row. The table's CHECK
 * constraint only admits ('validate','activate','deactivate','scan'), so the
 * row uses action='activate' and marks itself with metadata.kind =
 * 'offline_issue'. Nothing counts 'activate' rows in usage_logs. The machine
 * is intentionally NOT registered in license_machines and NO machine_changes
 * row is written, so abuse detection and the monthly change cap never see
 * offline issuance.
 *
 * Never logs the blob or the full license key.
 */

import type { Env } from '../types/env';
import { Errors, AppError } from '../lib/errors';
import {
  validateLicenseKey,
  normalizeLicenseKey,
  truncateMachineId,
  licenseKeyLogPrefix,
  isFuture,
  formatDate,
} from '../lib/license';
import { DEFAULT_LICENSE_SIGNING_KID } from '../lib/constants';
import { Plan, buildSecureLicenseLimits, getEnabledFeatures } from '../features';
import { signLicenseBlob, buildContractLicensePayload } from '../lib/license-blob-signer';
import { createDb, getLicenseByKey, logUsage } from '../lib/db';
import { verifyAdminApiKey } from './admin';
import { sql } from 'drizzle-orm';

/** nbf is backdated this far from iat so an air-gapped host with a slow clock can import. */
export const OFFLINE_NBF_BACKDATE_SECONDS = 48 * 60 * 60;
/** Upper bound on how far in the future an operator may set expires_at. */
export const OFFLINE_MAX_EXPIRY_DAYS = 400;
export const OFFLINE_LEDGER_KIND = 'offline_issue';

const MACHINE_ID_RE = /^[a-f0-9]{32}$/;
// ISO-8601 date-time with an explicit timezone (no ambiguous local times).
const ISO_TIMESTAMP_RE =
  /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:\d{2})$/;
const MAX_NOTE_LENGTH = 500;

interface OfflineBlobRequest {
  machine_id?: unknown;
  expires_at?: unknown;
  note?: unknown;
}

interface ParsedRequest {
  machineId: string;
  expSeconds: number;
  note: string | null;
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function parseOfflineRequest(raw: unknown, nowSeconds: number): ParsedRequest {
  if (typeof raw !== 'object' || raw === null || Array.isArray(raw)) {
    throw Errors.invalidRequest('Request body must be a JSON object');
  }
  const body = raw as OfflineBlobRequest;

  if (typeof body.machine_id !== 'string' || !MACHINE_ID_RE.test(body.machine_id)) {
    throw Errors.invalidRequest(
      'machine_id is required and must be 32 lowercase hex characters'
    );
  }

  if (typeof body.expires_at !== 'string' || !ISO_TIMESTAMP_RE.test(body.expires_at)) {
    throw Errors.invalidRequest(
      'expires_at is required and must be an ISO-8601 timestamp with a timezone'
    );
  }
  const expMs = Date.parse(body.expires_at);
  if (Number.isNaN(expMs)) {
    throw Errors.invalidRequest('expires_at is not a valid timestamp');
  }
  const expSeconds = Math.floor(expMs / 1000);
  if (expSeconds <= nowSeconds) {
    throw Errors.invalidRequest('expires_at must be in the future');
  }
  if (expSeconds > nowSeconds + OFFLINE_MAX_EXPIRY_DAYS * 86400) {
    throw Errors.invalidRequest(
      `expires_at must be at most ${OFFLINE_MAX_EXPIRY_DAYS} days from now`
    );
  }

  let note: string | null = null;
  if (body.note !== undefined && body.note !== null) {
    if (typeof body.note !== 'string' || body.note.length > MAX_NOTE_LENGTH) {
      throw Errors.invalidRequest(`note must be a string of at most ${MAX_NOTE_LENGTH} characters`);
    }
    note = body.note;
  }

  return { machineId: body.machine_id, expSeconds, note };
}

/** Same status semantics as validate-license's checkLicenseStatus, without side effects. */
function assertLicenseUsable(license: { status: string; currentPeriodEnd: string | null }): void {
  const periodEnd = license.currentPeriodEnd;
  switch (license.status) {
    case 'active':
      return;
    case 'expired':
      throw Errors.licenseExpired(formatDate(periodEnd ?? 'Unknown'));
    case 'revoked':
      throw Errors.licenseRevoked();
    case 'past_due':
      throw Errors.licensePastDue();
    case 'canceled':
      if (periodEnd && isFuture(periodEnd)) return;
      throw Errors.licenseExpired(formatDate(periodEnd ?? 'Unknown'));
    default:
      throw new AppError('FORBIDDEN', `License status '${license.status}' cannot be issued an offline blob`, 403);
  }
}

function errorResponse(error: unknown): Response {
  if (error instanceof AppError) {
    return json(error.toResponse(), error.statusCode);
  }
  throw error;
}

/**
 * POST /v1/admin/licenses/{key}/offline-blob
 */
export async function handleIssueOfflineBlob(
  request: Request,
  env: Env,
  licenseKey: string
): Promise<Response> {
  try {
    verifyAdminApiKey(request, env);

    validateLicenseKey(licenseKey);
    const normalizedKey = normalizeLicenseKey(licenseKey);

    let rawBody: unknown;
    try {
      rawBody = await request.json();
    } catch {
      throw Errors.invalidRequest('Invalid JSON body');
    }
    const nowSeconds = Math.floor(Date.now() / 1000);
    const { machineId, expSeconds, note } = parseOfflineRequest(rawBody, nowSeconds);

    // Fail CLOSED: unlike /validate, never degrade to "no blob but 200".
    if (!env.LICENSE_SIGNING_KEY) {
      console.error('[OFFLINE_BLOB] LICENSE_SIGNING_KEY not configured — refusing to issue');
      throw new AppError('SERVER_CONFIG_ERROR', 'License signing key is not configured', 503);
    }

    const db = createDb(env.DB);
    const license = await getLicenseByKey(db, normalizedKey);
    if (!license) {
      throw Errors.licenseNotFound();
    }
    if (license.plan !== 'sovereign') {
      throw new AppError(
        'FORBIDDEN',
        'Offline blobs can only be issued for Sovereign licenses',
        403
      );
    }
    assertLicenseUsable(license);

    const kid = env.LICENSE_SIGNING_KID || DEFAULT_LICENSE_SIGNING_KID;
    const planEnum = license.plan as Plan;
    const limits = buildSecureLicenseLimits(planEnum);
    const payload = buildContractLicensePayload({
      licenseKey: normalizedKey,
      plan: license.plan,
      machineId,
      kid,
      currentPeriodEnd: license.currentPeriodEnd,
      offlineGraceDays: limits.offline_grace_days,
      features: getEnabledFeatures(planEnum),
      limits,
      now: nowSeconds,
      explicitExp: expSeconds,
      nbfLeewaySeconds: OFFLINE_NBF_BACKDATE_SECONDS,
    });
    const blob = await signLicenseBlob(payload, env.LICENSE_SIGNING_KEY);

    // Ledger first: if this throws, the blob is never returned.
    await logUsage(db, {
      licenseId: license.id,
      machineId,
      action: 'activate',
      metadata: {
        kind: OFFLINE_LEDGER_KIND,
        exp: payload.exp,
        iat: payload.iat,
        nonce: payload.nonce,
        kid,
        note,
      },
    });

    console.warn(
      `[OFFLINE_BLOB] issued lic=${licenseKeyLogPrefix(normalizedKey)}... machine=${truncateMachineId(machineId)} exp=${payload.exp}`
    );

    return json({
      license_blob: blob,
      machine_id: machineId,
      expires_at: new Date(payload.exp * 1000).toISOString(),
      kid,
    });
  } catch (error) {
    return errorResponse(error);
  }
}

interface LedgerRow {
  id: string;
  machine_id: string | null;
  created_at: string;
  metadata: string | null;
}

/**
 * GET /v1/admin/licenses/{key}/offline-blobs — issuance ledger (no blobs).
 */
export async function handleListOfflineBlobs(
  request: Request,
  env: Env,
  licenseKey: string
): Promise<Response> {
  try {
    verifyAdminApiKey(request, env);

    validateLicenseKey(licenseKey);
    const normalizedKey = normalizeLicenseKey(licenseKey);

    const db = createDb(env.DB);
    const license = await getLicenseByKey(db, normalizedKey);
    if (!license) {
      throw Errors.licenseNotFound();
    }

    const rows = await db.all<LedgerRow>(sql`
      SELECT id, machine_id, created_at, metadata FROM usage_logs
      WHERE license_id = ${license.id}
        AND json_extract(metadata, '$.kind') = ${OFFLINE_LEDGER_KIND}
      ORDER BY created_at DESC
      LIMIT 200
    `);

    const entries = rows.map((r) => {
      const meta = r.metadata ? (JSON.parse(r.metadata) as Record<string, unknown>) : {};
      return {
        id: r.id,
        machine_id: r.machine_id,
        issued_at: r.created_at,
        exp: meta.exp ?? null,
        expires_at: typeof meta.exp === 'number' ? new Date(meta.exp * 1000).toISOString() : null,
        nonce: meta.nonce ?? null,
        kid: meta.kid ?? null,
        note: meta.note ?? null,
      };
    });

    return json({ license_key: normalizedKey, entries });
  } catch (error) {
    return errorResponse(error);
  }
}
