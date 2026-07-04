#!/usr/bin/env bash
#
# verify-webhook-signature.sh
# ---------------------------------------------------------------------------
# Verifies the PROD Stripe webhook endpoint's SIGNATURE-CHECKING logic without
# depending on Stripe at all (live mode has no "Send test events" / `stripe
# trigger`). It hand-rolls the exact scheme the worker verifies:
#
#     Stripe-Signature: t=<unix>,v1=<hex HMAC_SHA256(secret, "<t>.<body>")>
#     tolerance: 300s   (apps/api/src/handlers/stripe-webhook.ts)
#
# The secret is read ONLY from the environment. It is never hardcoded, never
# written to disk, never printed. Run it like this (value stays in YOUR shell):
#
#     STRIPE_WEBHOOK_SECRET='whsec_xxx' bash verify-webhook-signature.sh
#
# ---------------------------------------------------------------------------
# WHY THIS IS SAFE (creates no real data, touches no user):
#
# In the handler the order is:  verify signature (L772)  ->  JSON.parse (L787)
# ->  createDb (L790)  ->  process + markEventProcessed (L879, always writes).
#
# So a *correctly* signed request whose body is NOT valid JSON is ACCEPTED by
# the signature gate and then rejected by JSON.parse with 400 "Invalid JSON" —
# BEFORE any DB access. That 400 is positive proof the signature matched, with
# zero writes to prod D1. We exploit exactly that.
#
# Result matrix (this is the whole point):
#   POSITIVE probe (valid sig, non-JSON body):
#     400 "Invalid JSON"      -> signature ACCEPTED  => your secret == prod's  ✅
#     401 "Invalid signature" -> signature REJECTED  => secret MISMATCH        ❌
#     503 "Webhook not configured" -> prod STRIPE_WEBHOOK_SECRET not set        ⚠️
#   NEGATIVE probe (tampered sig): expect 401 "Invalid signature"
#   STALE probe  (valid hmac, t older than 5 min): expect 401
#
# A real, valid-signature checkout.session.completed IS built and signed below
# (per the task), but it is only SENT with a *tampered* signature (safe: 401,
# never parsed, never persisted). To actually send it with a valid signature —
# which WOULD create a test user + license row in prod for the test email —
# opt in explicitly with SEND_REAL_EVENT=1 (see bottom), then clean it up.
# ---------------------------------------------------------------------------
set -euo pipefail

ENDPOINT="https://api.replimap.com/v1/webhooks/stripe"
TEST_EMAIL="smoke-test@replimap-internal.test"

: "${STRIPE_WEBHOOK_SECRET:?Set it in your shell: STRIPE_WEBHOOK_SECRET='whsec_...' bash verify-webhook-signature.sh}"
command -v openssl >/dev/null 2>&1 || { echo "ERROR: openssl not found" >&2; exit 1; }
command -v curl    >/dev/null 2>&1 || { echo "ERROR: curl not found"    >&2; exit 1; }

now="$(date +%s)"

# HMAC-SHA256(secret, signed_payload) -> lowercase hex.  Reads exact bytes via
# printf '%s' (no trailing newline), matching what the worker signs.
hmac() { # $1 = signed payload string, $2 = secret
  printf '%s' "$1" | openssl dgst -sha256 -hmac "$2" | awk '{print $NF}'
}

# The checkout.session.completed event (task requirement 2). One line so the
# bytes we sign are exactly the bytes we send. created is stamped with `now`.
EVENT_JSON="$(printf '{"id":"evt_smoke_signature_test","object":"event","api_version":"2025-03-31","created":%s,"type":"checkout.session.completed","data":{"object":{"id":"cs_smoke_signature_test","object":"checkout.session","mode":"subscription","status":"complete","payment_status":"paid","customer":"cus_smoke_signature_test","customer_email":"%s","subscription":"sub_smoke_signature_test","amount_total":2900,"currency":"usd","metadata":{"plan":"pro","smoke_test":"true"}}}}' "$now" "$TEST_EMAIL")"

# A deliberately non-JSON body for the zero-write positive probe.
NONJSON_BODY="replimap-webhook-signature-smoke-test | intentionally-not-json | ${now}"

# POST helper: prints HTTP status + body, stores status in LAST_CODE.
LAST_CODE=""
send() { # $1 = label, $2 = body, $3 = Stripe-Signature header value
  local label="$1" body="$2" sig="$3" tmp code
  tmp="$(mktemp)"
  code="$(curl -sS -o "$tmp" -w '%{http_code}' -X POST "$ENDPOINT" \
    -H 'Content-Type: application/json' \
    -H "Stripe-Signature: ${sig}" \
    --data-binary "$body")"
  LAST_CODE="$code"
  printf '── %s\n   HTTP %s\n   %s\n\n' "$label" "$code" "$(cat "$tmp")"
  rm -f "$tmp"
}

echo "Target: $ENDPOINT"
echo "Clock : t=$now (tolerance ±300s)"
echo

# ── 1. POSITIVE (zero-write): valid signature over a non-JSON body ──────────
v1_ok="$(hmac "${now}.${NONJSON_BODY}" "$STRIPE_WEBHOOK_SECRET")"
send "POSITIVE  valid signature, non-JSON body   [expect 400 Invalid JSON = accepted]" \
     "$NONJSON_BODY" "t=${now},v1=${v1_ok}"
POS_CODE="$LAST_CODE"

# ── 2. NEGATIVE: tampered signature over the real checkout.session.completed ─
v1_bad="$(hmac "${now}.${EVENT_JSON}" 'whsec_deliberately_wrong_secret_000000')"
send "NEGATIVE  wrong-secret signature           [expect 401 Invalid signature]" \
     "$EVENT_JSON" "t=${now},v1=${v1_bad}"
NEG_CODE="$LAST_CODE"

# ── 3. NEGATIVE: valid HMAC but timestamp outside the 5-minute tolerance ────
t_old="$(( now - 600 ))"
v1_old="$(hmac "${t_old}.${NONJSON_BODY}" "$STRIPE_WEBHOOK_SECRET")"
send "NEGATIVE  stale timestamp (now-600s)        [expect 401, replay window]" \
     "$NONJSON_BODY" "t=${t_old},v1=${v1_old}"
STALE_CODE="$LAST_CODE"

# ── Optional: really send the valid-signed checkout.session.completed ───────
# WARNING: this WILL be processed and create a test user + license row in prod
# D1 for ${TEST_EMAIL}. Off by default. Enable only if you accept cleanup.
if [ "${SEND_REAL_EVENT:-0}" = "1" ]; then
  v1_real="$(hmac "${now}.${EVENT_JSON}" "$STRIPE_WEBHOOK_SECRET")"
  echo "!! SEND_REAL_EVENT=1 — this creates real test data in prod D1 !!"
  send "REAL      valid signature, real event      [expect 200; CREATES test data]" \
       "$EVENT_JSON" "t=${now},v1=${v1_real}"
fi

# ── Verdict ────────────────────────────────────────────────────────────────
echo "────────────────────────────────────────────────────────────"
if [ "$POS_CODE" = "400" ] && [ "$NEG_CODE" = "401" ] && [ "$STALE_CODE" = "401" ]; then
  echo "✅ PASS — signature verification works and YOUR secret matches prod's."
  echo "   (valid sig accepted → 400 parse error; bad sig & stale ts → 401)"
elif [ "$POS_CODE" = "401" ]; then
  echo "❌ FAIL — valid-per-your-secret signature was rejected (401)."
  echo "   Your STRIPE_WEBHOOK_SECRET does NOT match what prod holds (checklist §1.4)."
elif [ "$POS_CODE" = "503" ]; then
  echo "⚠️  prod STRIPE_WEBHOOK_SECRET is not configured (503). Set it, then re-run."
else
  echo "⚠️  Unexpected result. positive=$POS_CODE negative=$NEG_CODE stale=$STALE_CODE"
  echo "   Expected positive=400, negative=401, stale=401."
fi
