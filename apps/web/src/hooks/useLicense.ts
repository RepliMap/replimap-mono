'use client';

import { useAuth } from '@clerk/nextjs';
import { useCallback, useEffect, useState } from 'react';
import { getLicenseDetails, getOrProvisionLicenseKey } from '@/lib/api';
import type { LicenseDetails } from '@/types/license';

/**
 * Loads (and, on first visit, provisions) the signed-in user's license from
 * the browser.
 *
 * Why client-side: the request must originate from the user's own browser IP,
 * not from Vercel's server-side egress. Cloudflare Bot Fight Mode challenges
 * Vercel's cloud ASN (AWS) with a 403 before the request reaches the Worker,
 * but it does not challenge real browser traffic. Fetching here sidesteps that
 * entirely — no WAF exception or shared header required.
 *
 * Auth invariant (P0): identity comes solely from the Clerk session token
 * (forwarded as a bearer token); no client-supplied email is ever sent, so a
 * user can only ever provision/read their own license.
 */
export type LicenseState =
  | { status: 'loading' }
  // Provisioning failed — we could not even obtain a license key.
  | { status: 'error'; message: string }
  // Provisioning succeeded. `license` is null when the details lookup failed
  // (distinguished by `detailsFailed`) — the user still has a license.
  | {
      status: 'ready';
      licenseKey: string;
      license: LicenseDetails | null;
      detailsFailed: boolean;
    };

export function useLicense(): { state: LicenseState; reload: () => void } {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const [state, setState] = useState<LicenseState>({ status: 'loading' });
  const [nonce, setNonce] = useState(0);

  const reload = useCallback(() => setNonce((n) => n + 1), []);

  useEffect(() => {
    // Wait for Clerk to hydrate so getToken/isSignedIn are meaningful.
    if (!isLoaded) return;

    let cancelled = false;
    setState({ status: 'loading' });

    (async () => {
      const token = isSignedIn ? await getToken() : null;
      const keyResult = await getOrProvisionLicenseKey(token);
      if (cancelled) return;

      if (keyResult.status === 'error') {
        setState({ status: 'error', message: keyResult.message });
        return;
      }

      // Key acquired. Fetch details best-effort — a details failure must not be
      // mistaken for "no license" (the user provably has one at this point).
      let license: LicenseDetails | null = null;
      let detailsFailed = false;
      try {
        license = await getLicenseDetails(keyResult.licenseKey);
      } catch {
        detailsFailed = true;
      }
      if (!cancelled) {
        setState({
          status: 'ready',
          licenseKey: keyResult.licenseKey,
          license,
          detailsFailed,
        });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [isLoaded, isSignedIn, getToken, nonce]);

  return { state, reload };
}
