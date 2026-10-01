import { CheckoutPageContent } from '@/components/checkout/checkout-page-content';

// Static export: this page is prerendered at build time like every other
// route. Auth gating lives in the checkout/layout.tsx <RequireAuth> wrapper,
// and CheckoutForm's own useUser()/isLoaded check (checkout-page-content.tsx)
// already defers rendering checkout details until Clerk has resolved.
export default function CheckoutPage() {
  return <CheckoutPageContent />;
}
