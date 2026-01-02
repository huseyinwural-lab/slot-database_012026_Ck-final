import axios from 'axios';

// Prefer explicit env var; otherwise use same-origin (works with Nginx /api reverse proxy in prod images)
const BASE_URL = import.meta.env.VITE_API_URL
  || (typeof window !== 'undefined' ? `${window.location.origin}/api/v1` : '');

const api = axios.create({
  baseURL: BASE_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Tenant ID detection logic
// In production, this would parse subdomain (e.g., demo.casino.com -> demo)
// For now, we mock or read from localStorage
const getTenantId = () => {
    return localStorage.getItem('player_tenant_id') || 'default_casino';
};

// Request Interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('player_token');
    const tenantId = getTenantId();

    if (token && config.headers.Authorization !== null) {
      // Only attach auth if caller didn't explicitly disable it
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Send Tenant-ID header for multi-tenancy routing
    config.headers['X-Tenant-ID'] = tenantId;
    
    return config;
  },
  (error) => Promise.reject(error)
);

export default api;