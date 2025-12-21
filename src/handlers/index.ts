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
  handleTrackEvent,
} from './usage';

// Billing handlers
export {
  handleCreateCheckout,
  handleCreateBillingPortal,
} from './billing';

// User self-service handlers
export {
  handleGetOwnLicense,
  handleGetOwnMachines,
  handleResendKey,
} from './user';

// Features handlers
export {
  handleGetFeatures,
  handleCheckFeature,
  handleGetFeatureFlags,
} from './features';

// Metrics handlers
export {
  handleGetAdoption,
  handleGetConversion,
  handleGetRemediationImpact,
  handleGetSnapshotUsage,
  handleGetDepsUsage,
} from './metrics';
