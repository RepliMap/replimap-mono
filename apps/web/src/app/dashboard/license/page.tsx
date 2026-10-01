import { ClerkGate } from '@/components/auth-components';
import { LicensePageContent } from '@/components/dashboard/license-page-content';

// Auth gating lives in dashboard/layout.tsx's <RequireAuth> wrapper.
// License data is loaded client-side (from the browser) so Cloudflare Bot
// Fight Mode does not block the request. See LicensePageContent / useLicense.
//
// ClerkGate: LicensePageContent calls useLicense() -> useAuth(), which
// throws without a <ClerkProvider> ancestor. Static export prerenders this
// page at build time, and CI/local builds run with no Clerk key by design
// (see CLAUDE.md landmine 9), so LicensePageContent must not mount then.
export default function LicensePage() {
  return (
    <ClerkGate>
      <LicensePageContent />
    </ClerkGate>
  );
}
