import { currentUser } from '@clerk/nextjs/server';
import { redirect } from 'next/navigation';
import { LicensePageContent } from '@/components/dashboard/license-page-content';

export const dynamic = 'force-dynamic';

export default async function LicensePage() {
  const user = await currentUser();

  if (!user) {
    redirect('/sign-in');
  }

  // License data is loaded client-side (from the browser) so Cloudflare Bot
  // Fight Mode does not block the request. See LicensePageContent / useLicense.
  return <LicensePageContent />;
}
