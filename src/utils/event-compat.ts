/**
 * Event type compatibility layer for blast → deps rename.
 *
 * Old CLI versions may still send 'blast' events.
 * This module handles the mapping transparently.
 */

// =============================================================================
// Deprecated Event Mappings
// =============================================================================

/**
 * Deprecated event types that should be mapped to their new names
 */
export const DEPRECATED_EVENT_MAPPING: Record<string, string> = {
  blast: 'deps',
  blast_export: 'deps_export',
  blast_analyze: 'deps_explore',
  blast_list: 'deps_list',
};

/**
 * Deprecated feature names that should be mapped to their new names
 */
export const DEPRECATED_FEATURE_MAPPING: Record<string, string> = {
  blast: 'deps',
  blast_export: 'deps_export',
  blast_radius: 'deps',
};

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Normalize event type, mapping deprecated names to current.
 */
export function normalizeEventType(eventType: string): string {
  return DEPRECATED_EVENT_MAPPING[eventType] ?? eventType;
}

/**
 * Normalize feature name, mapping deprecated names to current.
 */
export function normalizeFeature(feature: string): string {
  return DEPRECATED_FEATURE_MAPPING[feature] ?? feature;
}

/**
 * Check if an event type is deprecated.
 */
export function isDeprecatedEvent(eventType: string): boolean {
  return eventType in DEPRECATED_EVENT_MAPPING;
}

/**
 * Check if a feature name is deprecated.
 */
export function isDeprecatedFeature(feature: string): boolean {
  return feature in DEPRECATED_FEATURE_MAPPING;
}

/**
 * Get deprecation warning message for an event type.
 */
export function getEventDeprecationWarning(oldName: string): string {
  const newName = DEPRECATED_EVENT_MAPPING[oldName];
  if (!newName) return '';

  return (
    `Warning: '${oldName}' is deprecated. Use '${newName}' instead. ` +
    `'${oldName}' will be removed in a future version.`
  );
}

/**
 * Get deprecation warning message for a feature.
 */
export function getFeatureDeprecationWarning(oldName: string): string {
  const newName = DEPRECATED_FEATURE_MAPPING[oldName];
  if (!newName) return '';

  return `Feature '${oldName}' is deprecated. Use '${newName}' instead.`;
}

/**
 * Get all deprecated event types and their mappings
 */
export function getDeprecatedEvents(): Array<{
  old: string;
  new: string;
  removalDate: string;
}> {
  return Object.entries(DEPRECATED_EVENT_MAPPING).map(([old, newName]) => ({
    old,
    new: newName,
    removalDate: '2025-06-01',
  }));
}

/**
 * Get rename information for API responses
 */
export function getRenameInfo(): {
  renamed_features: Array<{
    old_id: string;
    new_id: string;
    old_name: string;
    new_name: string;
    old_command: string;
    new_command: string;
    reason: string;
    migration_guide: string;
  }>;
  deprecated: Record<
    string,
    {
      replacement: string;
      removal_date: string;
      message?: string;
    }
  >;
} {
  return {
    renamed_features: [
      {
        old_id: 'blast',
        new_id: 'deps',
        old_name: 'Blast Radius Analyzer',
        new_name: 'Dependency Explorer',
        old_command: 'replimap blast analyze',
        new_command: 'replimap deps explore',
        reason:
          'Renamed to avoid misleading "safe deletion" claims. ' +
          'The feature now emphasizes exploration rather than guarantees.',
        migration_guide:
          'Replace "blast" with "deps" in all scripts and commands.',
      },
    ],
    deprecated: {
      blast: {
        replacement: 'deps',
        removal_date: '2025-06-01',
        message:
          'The "blast" command has been renamed to "deps". Please update your scripts.',
      },
      blast_analyze: {
        replacement: 'deps_explore',
        removal_date: '2025-06-01',
      },
      blast_export: {
        replacement: 'deps_export',
        removal_date: '2025-06-01',
      },
    },
  };
}
