/**
 * Handler exports for RepliMap Backend
 */

export { handleValidateLicense } from './validate-license';
export { handleActivateLicense } from './activate-license';
export { handleDeactivateLicense } from './deactivate-license';
export { handleStripeWebhook } from './stripe-webhook';

// Admin handlers
export {
  handleCreateLicense,
  handleRevokeLicense,
  handleGetLicense,
} from './admin';

// AWS account handlers
export {
  handleTrackAwsAccount,
  handleGetAwsAccounts,
} from './aws-accounts';

// Usage handlers
export {
  handleSyncUsage,
  handleGetUsage,
  handleGetUsageHistory,
  handleCheckQuota,
} from './usage';

// Billing handlers
export {
  handleCreateCheckout,
  handleCreateBillingPortal,
} from './billing';
