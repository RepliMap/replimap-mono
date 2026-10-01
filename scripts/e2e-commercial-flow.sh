#!/usr/bin/env bash
#
# e2e-commercial-flow.sh — orchestrate the full end-to-end commercial flow
#
# Boots: wrangler dev (API), next dev (web), stripe listen (webhook forwarder),
# then runs Playwright. Tears everything down on exit.
#
# Prereqs:
#   - pnpm install already run at the repo root
#   - stripe CLI installed + `stripe login` completed
#   - apps/web/.env.local populated with Clerk + Stripe test keys
#
# Usage:
#   ./scripts/e2e-commercial-flow.sh             # run all e2e specs
#   ./scripts/e2e-commercial-flow.sh community   # run community spec only
#   ./scripts/e2e-commercial-flow.sh pro-checkout
#

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

FILTER="${1:-}"
LOG_DIR="$ROOT/test-results/e2e-logs"
mkdir -p "$LOG_DIR"

# ─────────────────────────────────────────────────────────────────────
# Prereq checks
# ─────────────────────────────────────────────────────────────────────
ENV_FILE="$ROOT/apps/web/.env.local"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "❌ $ENV_FILE not found." >&2
  echo "   Copy from apps/web/.env.local.example and fill in values." >&2
  exit 1
fi

if ! grep -q "^NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=" "$ENV_FILE" || \
   ! grep -q "^CLERK_SECRET_KEY=" "$ENV_FILE"; then
  echo "❌ Clerk keys missing in apps/web/.env.local." >&2
  echo "   See apps/web/e2e/README.md." >&2
  exit 1
fi

if ! command -v stripe >/dev/null 2>&1; then
  echo "⚠  Stripe CLI not found on PATH — pro-checkout.spec will fail." >&2
  echo "   Install: https://stripe.com/docs/stripe-cli" >&2
  echo "   (Continuing — community-signup.spec doesn't need Stripe.)"
fi

# ─────────────────────────────────────────────────────────────────────
# Background processes
# ─────────────────────────────────────────────────────────────────────
API_PID=""
STRIPE_PID=""

cleanup() {
  local code=$?
  echo ""
  echo "→ Cleaning up background processes…"
  [[ -n "$API_PID" ]] && kill "$API_PID" 2>/dev/null || true
  [[ -n "$STRIPE_PID" ]] && kill "$STRIPE_PID" 2>/dev/null || true
  wait 2>/dev/null || true
  exit "$code"
}
trap cleanup EXIT INT TERM

echo "→ Starting wrangler dev (API) on :8787…"
(cd "$ROOT/apps/api" && pnpm dev --port 8787 --local) \
  > "$LOG_DIR/api.log" 2>&1 &
API_PID=$!

# Wait for API to be ready
for i in {1..30}; do
  if curl -sf http://localhost:8787/health >/dev/null 2>&1; then
    echo "  ✓ API up"
    break
  fi
  sleep 1
done

echo "→ Starting stripe listen (webhook forwarder)…"
stripe listen \
  --forward-to localhost:8787/v1/webhooks/stripe \
  --events checkout.session.completed,customer.subscription.created,customer.subscription.updated,customer.subscription.deleted,invoice.paid,invoice.payment_failed,charge.refunded \
  > "$LOG_DIR/stripe.log" 2>&1 &
STRIPE_PID=$!
sleep 3

# Extract and export the webhook signing secret from stripe listen output
WEBHOOK_SECRET=$(grep -oE 'whsec_[A-Za-z0-9]+' "$LOG_DIR/stripe.log" | head -n1 || true)
if [[ -n "$WEBHOOK_SECRET" ]]; then
  echo "  ✓ Stripe listening (webhook secret captured)"
  export STRIPE_WEBHOOK_SECRET="$WEBHOOK_SECRET"
else
  echo "  ⚠ Could not capture Stripe webhook secret — using existing STRIPE_WEBHOOK_SECRET."
fi

# ─────────────────────────────────────────────────────────────────────
# Playwright
# ─────────────────────────────────────────────────────────────────────
echo "→ Running Playwright…"
cd "$ROOT/apps/web"
if [[ -n "$FILTER" ]]; then
  pnpm e2e "$FILTER"
else
  pnpm e2e
fi
