# Deploy Runbook: Ed25519 License-Blob Signing (Offline License #2, Phase 4)

> **STATE UPDATE 2026-07-08 (post-execution):** The signing path IS live on
> both dev and prod (secret-change + deploys at 2026-07-07T22:09-22:37Z;
> `LICENSE_SIGNING_KEY` present in both secret stores). Verified end-to-end
> on prod 2026-07-08: `/v1/license/validate` returns a `license_blob` that
> CLI v0.4.2 verifies and caches (team activation succeeded). The
> "Not yet deployed" statements below describe the state when this runbook
> was written and are OBSOLETE. Two follow-ups discovered during
> verification: (1) signer sets `nbf = iat = now` with zero leeway — a
> client whose clock is even 1s behind rejects a fresh blob
> ("License not valid until ..."); CLI-side 300s leeway fix in the
> `replimap` repo; consider backdating `nbf` by 60-300s at the NEXT worker
> deploy (do not deploy solely for this). (2) The signing-code commit cited
> below as `e7f2cff` now lives in history as `cd58f29` (rebase, identical
> content).

Manual go-live steps for the License Blob Format Contract v1 signing path.

**State when this runbook was written:**

- Worker side (this repo): `/v1/license/validate` signs a contract-compliant
  `license_blob` when `LICENSE_SIGNING_KEY` is configured; fails open (omits
  the field, never 500s) when it is not. Commit `e7f2cff`. **Not yet
  deployed to dev or prod.**
- CLI side (`replimap` repo): activation hard-requires `license_blob` and
  verifies it locally; the cache stores the blob and re-verifies on load;
  default endpoint is `https://api.replimap.com/v1`
  (`REPLIMAP_LICENSE_API` overrides). Commit `a5c1fde`. **Not yet released
  to PyPI** — the released `0.4.1` predates it and ignores `license_blob`.
- No D1 schema change is involved anywhere in this rollout. The signer only
  reads existing `licenses` columns (`license_key`, `plan`, `status`,
  `current_period_end`). **Never run `wrangler d1 migrations apply` against
  prod D1** (repo CLAUDE.md landmine #1) — this rollout gives you no reason
  to.

**Hard ordering constraint:** the Worker (dev → prod) must be deployed and
verified **before** the new CLI is released. A blob-verifying CLI against a
non-signing Worker fails every activation with "server did not return a
signed license". The reverse order is safe: a signing Worker is invisible to
old clients (additive envelope).

---

## 0. Environment map (from `apps/api/wrangler.toml`, verified 2026-07-08)

| | dev | prod |
|---|---|---|
| Worker name | `replimap-api` (top-level default) | `replimap-api-prod` (`[env.prod]`) |
| Domain | api-dev.replimap.com | api.replimap.com |
| D1 | `replimap-dev` (`212335fc-ffeb-40d2-8794-c0d84a0991a1`) | `replimap-prod` (`0cda6e12-5087-4b1a-8dfe-207960c88f2d`) |
| KV `CACHE` | `32520e34…` | `705a8c1a…` |
| Deploy | `pnpm deploy` (from `apps/api/`) | `pnpm deploy:prod` |
| Secrets | `npx wrangler secret put <NAME>` | `npx wrangler secret put <NAME> --env prod` |

**Data-consistency finding: dev and prod do NOT share license data.**
Different D1 database IDs, different KV namespaces. Real purchased licenses
(including the live $29 Pro from the prod E2E smoke test) exist **only** in
`replimap-prod`. Dev D1 holds dev/test rows and is restored to baseline
after validation runs. Consequences:

- Step 3b (dev end-to-end test) needs a license row **in dev D1**. Check
  first; provision one via the normal dev flow if absent.
- No backfill/re-issue is needed on prod: everything a paying customer
  activated is already in prod D1. Nothing about this rollout moves data.

Check commands (SELECT only — safe on both):

```bash
cd apps/api
npx wrangler d1 execute replimap-dev  --remote            --command "SELECT license_key, plan, status, current_period_end FROM licenses ORDER BY created_at DESC LIMIT 10"
npx wrangler d1 execute replimap-prod --remote --env prod --command "SELECT license_key, plan, status, current_period_end FROM licenses ORDER BY created_at DESC LIMIT 10"
```

---

## 1. Prerequisites

- [ ] Production Ed25519 keypair generated offline; **private key** (PEM
      PKCS8, `-----BEGIN PRIVATE KEY-----`) stored in the password manager.
      It must never appear in either repo, in shell history, or in logs.
- [ ] **Public key** (PEM SubjectPublicKeyInfo, `-----BEGIN PUBLIC KEY-----`)
      at hand for the CLI side.

### 1.1 Fill the public key into the CLI's key registry

File: `replimap/licensing/crypto/keys.py` (replimap repo).

- `PUBLIC_KEYS` dict starts at **line 46**; the `"key-2024-01"` placeholder
  entry is **lines 48–50** (currently
  `MCowBQYDK2VwAyEAREPLACE_WITH_YOUR_ACTUAL_PUBLIC_KEY_HERE_32BYTES`).
- `CURRENT_KEY_ID` is **line 58**.

Replace the placeholder PEM body with the real public key. It must be the
**PEM-armored SubjectPublicKeyInfo** form — NOT the raw 32-byte key, NOT
hex, NOT bare base64:

```python
    PUBLIC_KEYS: dict[str, bytes] = {
        # Current active key (2024)
        "key-2024-01": b"""-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEA<44-char-base64-ending-in-=>
-----END PUBLIC KEY-----""",
    }
```

(A valid Ed25519 SPKI PEM body is always one line of 44 base64 chars
starting `MCowBQYDK2VwAyEA`.)

**If you rename the kid** (e.g. to `key-2026-07`): change the dict key AND
`CURRENT_KEY_ID` (line 58) AND set the Worker's `LICENSE_SIGNING_KID` secret
to the same string (step 2). If you keep `key-2024-01`, no
`LICENSE_SIGNING_KID` is needed — it's the Worker's built-in default
(`DEFAULT_LICENSE_SIGNING_KID`, `apps/api/src/lib/constants.ts`). The kid in
the blob and the registry key must match exactly or every verification fails
with `LicenseSignatureError: unknown key`.

Do **not** commit/push keys.py yet — that happens in step 3f, after both
Workers are live (push to the replimap repo auto-releases).

---

## 2. Private key injection — dev first

From `apps/api/` in this repo. `wrangler secret put` reads the value from
stdin, which is the only sane way to pass a multi-line PEM:

```bash
cd apps/api

# Write the PEM to a throwaway file OUTSIDE any repo, from the password
# manager. Then:
npx wrangler secret put LICENSE_SIGNING_KEY < /path/to/license-signing-key.pem
shred -u /path/to/license-signing-key.pem   # remove immediately after

# Only if you renamed the kid in step 1.1:
printf 'key-2026-07' | npx wrangler secret put LICENSE_SIGNING_KID
```

Bare `wrangler secret put` targets the **dev** worker (`replimap-api`) by
design — safety-first default per wrangler.toml. Verify:

```bash
npx wrangler secret list        # should now include LICENSE_SIGNING_KEY
```

Setting the secret before deploying the new code is deliberately safe: the
currently-deployed dev worker doesn't read it.

---

## 3. Go-live sequence (order is binding)

### 3a. Deploy the signing-capable Worker to dev

```bash
cd apps/api
pnpm typecheck && pnpm lint && pnpm test    # CI gate — must be green
pnpm deploy                                  # → replimap-api / api-dev.replimap.com
```

**Verify** (needs any license row present in dev D1 — see §0 check):

```bash
curl -s https://api-dev.replimap.com/v1/license/validate \
  -X POST -H 'Content-Type: application/json' \
  -d '{"license_key":"<DEV-TEST-KEY>","machine_id":"'"$(openssl rand -hex 16)"'","cli_version":"1.0.0"}' \
  | jq -r '.license_blob' | head -c 80
# Expect: a base64url string (two dot-separated segments), NOT "null".
```

Note: `curl -I` / HEAD returns 404 on this Worker (routes are
method-specific). Health check is `curl https://api-dev.replimap.com/health`
with GET.

### 3b. Real-CLI end-to-end test against dev

From a local checkout of the replimap repo **with the real public key
already filled into keys.py** (step 1.1, uncommitted):

```bash
cd /path/to/replimap
REPLIMAP_LICENSE_API=https://api-dev.replimap.com/v1 \
  uv run replimap license activate <DEV-TEST-KEY>
# Expect: activation succeeds — this now implies the blob was returned AND
# locally signature-verified (Phase 3 hard-requires it).

# Offline re-verification from cache (~/.replimap/license.json now holds
# the blob). Point the API at an unroutable address to prove zero network:
REPLIMAP_LICENSE_API=http://127.0.0.1:9/v1 uv run replimap license status
# Expect: correct plan/status shown, no network error — verified from the
# cached blob only.
```

If activation fails with `LicenseSignatureError` here, the public key in
keys.py does not match the private key in the dev Worker secret (or the kid
mismatches). Fix before proceeding — do not touch prod.

### 3c. Dev/prod data-consistency check

Already adjudicated in §0: **not shared** (separate D1 + KV per
environment). Run the two SELECTs in §0 and confirm:

- [ ] The prod `licenses` table contains the expected real licenses
      (David's live Pro license from the smoke test at minimum).
- [ ] Nothing needs re-issuing: prod-activated licenses already live in
      prod D1; this rollout adds no rows and no columns.

### 3d. Private key into prod + deploy prod

Same private key (one keypair serves both workers — deployment difference
is which secret store holds it, not the code):

```bash
cd apps/api
npx wrangler secret put LICENSE_SIGNING_KEY --env prod < /path/to/license-signing-key.pem
shred -u /path/to/license-signing-key.pem
# If using a renamed kid:
printf 'key-2026-07' | npx wrangler secret put LICENSE_SIGNING_KID --env prod

npx wrangler secret list --env prod         # confirm present
pnpm deploy:prod                            # → replimap-api-prod / api.replimap.com
```

### 3e. Repeat the real-CLI test against prod

```bash
curl -s https://api.replimap.com/v1/license/validate \
  -X POST -H 'Content-Type: application/json' \
  -d '{"license_key":"<REAL-LICENSE-KEY>","machine_id":"'"$(openssl rand -hex 16)"'","cli_version":"1.0.0"}' \
  | jq -r '.license_blob' | head -c 80
```

⚠ The random `machine_id` above registers a device slot against that
license (Pro = 2 machines, 3 changes/month). Prefer running the CLI test
from the machine you actually use, so the fingerprint is your real one:

```bash
uv run replimap license activate <REAL-LICENSE-KEY>   # default endpoint IS prod now
REPLIMAP_LICENSE_API=http://127.0.0.1:9/v1 uv run replimap license status
```

### 3f. Release the CLI (last)

Only after 3e passes:

```bash
cd /path/to/replimap
# Commit together: keys.py with the real public key (step 1.1) +
# docs/security/outbound-network-surface.md updates (section 5 below).
git add replimap/licensing/crypto/keys.py docs/security/outbound-network-surface.md
git commit -m "feat: production Ed25519 public key + outbound-surface declaration update (offline license #2, Phase 4)"
git push        # → auto-release to PyPI
```

---

## 4. Old-client compatibility

- **Already-installed 0.4.1 clients are unaffected by the Worker deploys.**
  The envelope is additive: 0.4.1 never reads `license_blob`, so a signing
  (or non-signing) Worker looks identical to it. Deploy the Workers any
  time.
- **The new CLI (blob-verifying) must ship after both Workers sign** —
  otherwise every `activate` fails with "server did not return a signed
  license" (deliberate fail-closed on the client, contract §7).
- Users upgrading 0.4.1 → new: their existing `~/.replimap/license.json`
  has no blob, so the new client treats it as unverified — **one-time
  re-activation (`replimap license activate <key>`) is required after
  upgrading**; mention this in the release notes.

---

## 5. Security declaration update (pre-drafted, ships with step 3f)

File: `docs/security/outbound-network-surface.md` (replimap repo). Two
edits, copy-paste ready:

**① Section 5, replace the roadmap bullet** (last bullet, currently
"Roadmap note: license activation is planned to move to offline signature
verification…"):

```markdown
- License activation returns an Ed25519-signed license file (`license_blob`),
  which the CLI verifies locally against a public key embedded in the source
  (`replimap/licensing/crypto/keys.py`) — no secret exists on the client.
  The signed file is cached in `~/.replimap/license.json` and re-verified
  locally on every load, so day-to-day operation performs zero network I/O;
  row 2.1 is a one-time activation call with local cryptographic
  verification thereafter.
```

**② Endpoint wording — two spots referencing "Cloudflare Workers":**

Section 2, row 1, replace the endpoint cell's opening with:

```markdown
The RepliMap license service at `https://api.replimap.com` (the exact URL is
a constant in `replimap/licensing/manager.py`, overridable via
`REPLIMAP_LICENSE_API`)
```

Section 5, replace the bullet "The license service currently runs on a
Cloudflare Workers endpoint … migration to a first-party custom domain is
planned…" with:

```markdown
- The license service is served at the first-party domain
  `api.replimap.com`. The endpoint you allowlist is the one constant in
  `licensing/manager.py` — there is exactly one; `REPLIMAP_LICENSE_API`
  overrides it for internal proxies.
```

---

## 6. Rollback

| Step gone wrong | Rollback | Notes |
|---|---|---|
| Dev Worker deploy (3a) | Redeploy previous version: `git checkout <prev-sha> -- .` is unnecessary — `cd apps/api && npx wrangler rollback` (or `git checkout <prev-sha>; pnpm deploy`) | Fail-open design means even a half-configured signer never breaks old clients; worst case the blob is absent |
| Prod Worker deploy (3d) | Same, with `--env prod` / `pnpm deploy:prod` from the previous commit | Same fail-open guarantee |
| Secret set wrongly (bad PEM) | Worker logs `[LICENSE_BLOB] Failed to sign license blob` and omits the field — old clients unaffected, new clients can't activate. Re-run `wrangler secret put` with the correct PEM | `wrangler tail` / `wrangler tail --env prod` to observe |
| **Wrong public key in keys.py** | Symptom: **every** `activate` on the new CLI fails with `LicenseSignatureError` (server-signed blob doesn't verify). Fix keys.py, re-release | This is why 3b gates 3f — the mismatch must be caught on dev before any client ships |
| New CLI release broken | Users: `pip install replimap==0.4.1` (pre-blob client, works against signing Workers unchanged) | Then fix-forward |
| kid mismatch (blob kid ∉ PUBLIC_KEYS) | Same symptom as wrong public key. Either set `LICENSE_SIGNING_KID` to a registered kid or add the kid to keys.py and re-release | Keep kid changes atomic across both sides |

---

## 7. Verification checklist (one command per step)

- [ ] **Secret on dev**: `cd apps/api && npx wrangler secret list` → contains `LICENSE_SIGNING_KEY`
- [ ] **Dev signs**: `curl -s https://api-dev.replimap.com/v1/license/validate -X POST -H 'Content-Type: application/json' -d '{"license_key":"<DEV-TEST-KEY>","machine_id":"<32-hex>","cli_version":"1.0.0"}' | jq -e '.license_blob | test("^[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+$")'` → `true`
- [ ] **CLI verifies against dev**: `REPLIMAP_LICENSE_API=https://api-dev.replimap.com/v1 replimap license activate <DEV-TEST-KEY>` → success
- [ ] **Offline re-verify**: `REPLIMAP_LICENSE_API=http://127.0.0.1:9/v1 replimap license status` → correct plan, no network error
- [ ] **Data check**: the two D1 SELECTs in §0 → prod rows intact, no schema drift
- [ ] **Secret on prod**: `npx wrangler secret list --env prod` → contains `LICENSE_SIGNING_KEY`
- [ ] **Prod signs**: same curl as dev against `https://api.replimap.com` with a real key → `license_blob` present
- [ ] **CLI against prod (default endpoint)**: `replimap license activate <REAL-KEY>` → success, then offline `license status` → success
- [ ] **Old client unaffected**: with 0.4.1 installed: `replimap license status` → unchanged behavior
- [ ] **Post-release**: fresh `pip install replimap` (new version) → `replimap license activate <key>` works end-to-end
