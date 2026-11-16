'use client';

import { useState } from 'react';
import { useAuth } from '@clerk/clerk-react';
import { createBillingPortalSession } from '@/lib/api';
import { Button } from '@/components/ui/button';

/**
 * Opens the Stripe billing portal (cancel, change card, invoices) for the
 * signed-in license owner. The API checks the Clerk session against the owner.
 */
export function ManageBillingButton({ licenseKey }: { licenseKey: string }) {
  const { getToken } = useAuth();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function openPortal() {
    setPending(true);
    setError(null);
    try {
      const { portal_url } = await createBillingPortalSession(
        licenseKey,
        window.location.href,
        await getToken()
      );
      window.location.assign(portal_url);
    } catch {
      setError('Could not open the billing portal. Please try again.');
      setPending(false);
    }
  }

  return (
    <div>
      <Button variant="outline" onClick={openPortal} disabled={pending}>
        {pending ? 'Opening…' : 'Manage billing'}
      </Button>
      {error && (
        <p role="alert" className="mt-2 text-sm text-red-500">
          {error}
        </p>
      )}
    </div>
  );
}
