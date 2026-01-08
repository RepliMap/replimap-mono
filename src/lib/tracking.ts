/**
 * UTM and referral tracking for analytics and Stripe metadata.
 */

const UTM_PARAMS = [
  "utm_source",
  "utm_medium",
  "utm_campaign",
  "utm_content",
  "utm_term",
];
const STORAGE_KEY = "replimap_attribution";

export interface Attribution {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_content?: string;
  utm_term?: string;
  referrer?: string;
  landing_page?: string;
  first_visit?: string;
}

export function captureAttribution(): void {
  if (typeof window === "undefined") return;

  // Don't overwrite existing attribution
  const existing = getAttribution();
  if (existing.first_visit) return;

  const params = new URLSearchParams(window.location.search);
  const attribution: Attribution = {
    first_visit: new Date().toISOString(),
    landing_page: window.location.pathname,
    referrer: document.referrer || undefined,
  };

  // Capture UTM params
  UTM_PARAMS.forEach((param) => {
    const value = params.get(param);
    if (value) {
      attribution[param as keyof Attribution] = value;
    }
  });

  // Store in localStorage
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(attribution));
  } catch {
    // localStorage might be unavailable
    console.warn("Failed to store attribution:", e);
  }
}

export function getAttribution(): Attribution {
  if (typeof window === "undefined") return {};

  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch {
    return {};
  }
}

export function getAttributionForStripe(): Record<string, string> {
  const attribution = getAttribution();
  const result: Record<string, string> = {};

  // Flatten for Stripe metadata (max 500 chars per value)
  if (attribution.utm_source) result.utm_source = attribution.utm_source;
  if (attribution.utm_medium) result.utm_medium = attribution.utm_medium;
  if (attribution.utm_campaign) result.utm_campaign = attribution.utm_campaign;
  if (attribution.referrer)
    result.referrer = attribution.referrer.slice(0, 200);
  if (attribution.landing_page) result.landing_page = attribution.landing_page;

  return result;
}

export function clearAttribution(): void {
  if (typeof window === "undefined") return;

  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    console.warn("Failed to clear attribution:", e);
  }
}
