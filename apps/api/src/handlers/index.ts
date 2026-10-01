/**
 * Handler exports for RepliMap Backend
 */

export { handleValidateLicense } from './validate-license';
export { handleDeactivateLicense } from './deactivate-license';
export { handleStripeWebhook } from './stripe-webhook';

// Admin handlers
export {
  handleCreateLicense,
  handleRevokeLicense,
  handleGetLicense,
  handleGetStats,
} from './admin';

// Billing handlers
export {
  handleCreateCheckout,
  handleCreateBillingPortal,
} from './billing';

// Post-checkout license lookup (used by /checkout/success page)
export { handleGetCheckoutLicense } from './checkout-license';

// Community tier auto-provisioning (used on first dashboard load)
export { handleProvisionCommunity } from './provision-community';

// User self-service handlers
export {
  handleGetOwnLicense,
  handleGetOwnMachines,
  handleResendKey,
} from './user';
