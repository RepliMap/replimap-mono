'use client';

import { useCallback, useEffect, useState } from 'react';
import { getMachines } from '@/lib/api';
import type { MachinesResponse } from '@/types/license';

/**
 * Loads the devices activated on a license from the browser.
 *
 * Browser-side for the same reason as useLicense: Cloudflare Bot Fight Mode
 * challenges Vercel's SSR egress before it reaches the Worker, but not real
 * browser traffic. Owner-scoped by license-key possession — the API only
 * returns machines belonging to the presented key's license.
 */
export type MachinesState =
  | { status: 'idle' } // no license key yet — nothing to load
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; data: MachinesResponse };

export function useMachines(licenseKey: string | null): {
  state: MachinesState;
  reload: () => void;
} {
  const [state, setState] = useState<MachinesState>({ status: 'idle' });
  const [nonce, setNonce] = useState(0);

  const reload = useCallback(() => setNonce((n) => n + 1), []);

  useEffect(() => {
    if (!licenseKey) {
      setState({ status: 'idle' });
      return;
    }

    let cancelled = false;
    setState({ status: 'loading' });

    (async () => {
      try {
        const data = await getMachines(licenseKey);
        if (!cancelled) setState({ status: 'ready', data });
      } catch (error) {
        console.error('[api] /v1/me/machines failed:', error);
        if (!cancelled) {
          setState({
            status: 'error',
            message:
              'Could not load your devices right now. Refresh to try again.',
          });
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [licenseKey, nonce]);

  return { state, reload };
}
