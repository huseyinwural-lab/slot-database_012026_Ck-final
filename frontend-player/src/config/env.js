const apiUrl = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL;
if (!apiUrl) {
  throw new Error('VITE_API_URL is required');
}

export const env = {
  apiUrl,
  crispWebsiteId: import.meta.env.VITE_CRISP_WEBSITE_ID || '',
  stripePublishableKey: import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || '',
};
