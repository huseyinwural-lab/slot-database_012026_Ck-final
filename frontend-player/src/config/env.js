const rawApiUrl = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL;
if (!rawApiUrl) {
  throw new Error('VITE_API_URL is required');
}

const normalizedApiUrl = rawApiUrl.endsWith('/api/v1')
  ? rawApiUrl
  : `${rawApiUrl.replace(/\/$/, '')}/api/v1`;

export const env = {
  apiUrl: normalizedApiUrl,
  crispWebsiteId: import.meta.env.VITE_CRISP_WEBSITE_ID || '',
  stripePublishableKey: import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || '',
};
