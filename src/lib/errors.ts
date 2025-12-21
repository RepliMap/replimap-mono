/**
 * Error handling utilities for RepliMap Backend
 */

import type { ErrorCode, ErrorResponse } from '../types';

// ============================================================================
// AppError Class
// ============================================================================

export class AppError extends Error {
  readonly errorCode: ErrorCode;
  readonly statusCode: number;
  readonly action?: string;
  readonly machines?: string[];
  readonly limit?: number;
  readonly resetsAt?: string;
  readonly retryAfter?: number;

  constructor(
    errorCode: ErrorCode,
    message: string,
    statusCode: number = 400,
    options?: {
      action?: string;
      machines?: string[];
      limit?: number;
      resetsAt?: string;
      retryAfter?: number;
    }
  ) {
    super(message);
    this.name = 'AppError';
    this.errorCode = errorCode;
    this.statusCode = statusCode;
    this.action = options?.action;
    this.machines = options?.machines;
    this.limit = options?.limit;
    this.resetsAt = options?.resetsAt;
    this.retryAfter = options?.retryAfter;
  }

  toResponse(): ErrorResponse {
    const response: ErrorResponse = {
      valid: false,
      error_code: this.errorCode,
      message: this.message,
      support_id: generateSupportId(),
    };

    if (this.action) response.action = this.action;
    if (this.machines) response.machines = this.machines;
    if (this.limit !== undefined) response.limit = this.limit;
    if (this.resetsAt) response.resets_at = this.resetsAt;
    if (this.retryAfter !== undefined) response.retry_after = this.retryAfter;

    return response;
  }
}

// ============================================================================
// Common Error Factories
// ============================================================================

export const Errors = {
  licenseNotFound(): AppError {
    return new AppError(
      'LICENSE_NOT_FOUND',
      'License key not found',
      404
    );
  },

  licenseExpired(expiredAt: string): AppError {
    return new AppError(
      'LICENSE_EXPIRED',
      `Your subscription expired on ${expiredAt}`,
      403,
      { action: 'Renew at https://replimap.io/renew' }
    );
  },

  licenseCanceled(validUntil: string): AppError {
    return new AppError(
      'LICENSE_CANCELED',
      `Your subscription is canceled but valid until ${validUntil}`,
      403,
      { action: 'Resubscribe at https://replimap.io/renew' }
    );
  },

  licensePastDue(): AppError {
    return new AppError(
      'LICENSE_PAST_DUE',
      'Payment failed. Please update your payment method.',
      403,
      { action: 'Update payment at https://replimap.io/dashboard/billing' }
    );
  },

  licenseRevoked(): AppError {
    return new AppError(
      'LICENSE_REVOKED',
      'This license has been revoked. Please contact support.',
      403,
      { action: 'Contact support at https://replimap.io/support' }
    );
  },

  machineLimitExceeded(machines: string[], limit: number): AppError {
    return new AppError(
      'MACHINE_LIMIT_EXCEEDED',
      `This license is already active on ${limit} machines`,
      403,
      {
        action: 'Deactivate a machine at https://replimap.io/dashboard or upgrade',
        machines,
        limit,
      }
    );
  },

  machineChangeLimitExceeded(resetsAt: string): AppError {
    return new AppError(
      'MACHINE_CHANGE_LIMIT',
      'Monthly machine change limit (3) reached',
      403,
      {
        action: 'Wait until next month or contact support',
        resetsAt,
      }
    );
  },

  awsAccountLimitExceeded(limit: number): AppError {
    return new AppError(
      'AWS_ACCOUNT_LIMIT_EXCEEDED',
      `AWS account limit (${limit}) reached for your plan`,
      403,
      { action: 'Upgrade at https://replimap.io/upgrade', limit }
    );
  },

  rateLimitExceeded(retryAfter: number): AppError {
    return new AppError(
      'RATE_LIMIT_EXCEEDED',
      'Too many requests',
      429,
      { retryAfter }
    );
  },

  invalidRequest(details: string): AppError {
    return new AppError(
      'INVALID_REQUEST',
      details,
      400
    );
  },

  invalidLicenseFormat(): AppError {
    return new AppError(
      'INVALID_LICENSE_FORMAT',
      'Invalid license key format. Expected: RM-XXXX-XXXX-XXXX-XXXX',
      400
    );
  },

  invalidMachineFormat(): AppError {
    return new AppError(
      'INVALID_MACHINE_FORMAT',
      'Invalid machine ID format. Expected: 32 character hex string',
      400
    );
  },

  webhookSignatureInvalid(): AppError {
    return new AppError(
      'WEBHOOK_SIGNATURE_INVALID',
      'Invalid webhook signature',
      400
    );
  },

  notFound(message: string = 'Resource not found'): AppError {
    return new AppError(
      'NOT_FOUND',
      message,
      404
    );
  },

  unauthorized(message: string = 'Unauthorized'): AppError {
    return new AppError(
      'UNAUTHORIZED',
      message,
      401
    );
  },

  internal(message: string = 'An unexpected error occurred'): AppError {
    return new AppError(
      'INTERNAL_ERROR',
      message,
      500
    );
  },

  // Alias for backwards compatibility
  internalError(message: string = 'An unexpected error occurred'): AppError {
    return this.internal(message);
  },
};

// ============================================================================
// Support ID Generation
// ============================================================================

/**
 * Generate a unique support ID for error tracking
 * Format: ERR-{timestamp}-{random}
 */
export function generateSupportId(): string {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).substring(2, 8);
  return `ERR-${timestamp}-${random}`.toUpperCase();
}

// ============================================================================
// Error Handler
// ============================================================================

/**
 * Convert any error to a Response
 */
export function errorToResponse(error: unknown): Response {
  if (error instanceof AppError) {
    return new Response(JSON.stringify(error.toResponse()), {
      status: error.statusCode,
      headers: {
        'Content-Type': 'application/json',
        ...(error.retryAfter ? { 'Retry-After': String(error.retryAfter) } : {}),
      },
    });
  }

  // Log unexpected errors
  console.error('Unexpected error:', error);

  // Return generic error for unexpected errors
  const appError = Errors.internalError();
  return new Response(JSON.stringify(appError.toResponse()), {
    status: 500,
    headers: { 'Content-Type': 'application/json' },
  });
}
