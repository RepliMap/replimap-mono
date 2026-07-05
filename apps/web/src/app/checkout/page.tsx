import { CheckoutPageContent } from '@/components/checkout/checkout-page-content';

// The checkout flow depends on the live Clerk session and query params —
// statically prerendering it at build time is meaningless, and it broke CI:
// builds without Clerk credentials skip <ClerkProvider> (see
// clerk-provider.tsx), so the client useUser() inside the page threw
// "useUser can only be used within the <ClerkProvider />" during
// `next build`'s SSG pass. force-dynamic must live here, in the server page
// file — route segment config is not reliably honored inside 'use client'
// files.
export const dynamic = 'force-dynamic';

export default function CheckoutPage() {
  return <CheckoutPageContent />;
}
