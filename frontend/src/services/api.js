import axios from 'axios';

// Prefer explicit env var; otherwise use same-origin (works with Nginx /api reverse proxy in prod images)
const RAW_API_URL = process.env.REACT_APP_BACKEND_URL
  || (typeof window !== 'undefined' ? window.location.origin : '');

// Prevent mixed-content in HTTPS environments.
// If the app is served over HTTPS but the backend URL is HTTP (common misconfig), upgrade.
let API_URL = RAW_API_URL;
if (typeof window !== 'undefined' && window.location?.protocol === 'https:' && API_URL.startsWith('http://')) {
  API_URL = API_URL.replace(/^http:\/\//, 'https://');
}

const api = axios.create({
  baseURL: API_URL.endsWith('/api') ? API_URL : `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT token if available
api.interceptors.request.use((config) => {
  try {
    const token = typeof window !== 'undefined' ? localStorage.getItem('admin_token') : null;
    const tenantId = typeof window !== 'undefined' ? localStorage.getItem('impersonate_tenant_id') : null;

     
    config.headers = config.headers || {};

    if (token) {
       
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Owner impersonation: pass tenant context via header
    if (tenantId) {
       
      config.headers['X-Tenant-ID'] = tenantId;
    }
  } catch (e) {
    // localStorage not available; ignore
  }
  return config;
});
// Response Interceptor for Error Standardization
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const originalRequest = error.config;
    
    // Standardize Error Object
    const raw = error.response?.data || {};
    const detail = raw.detail || {};

    const standardizedError = {
        code: raw.error_code || detail.error_code || 'UNKNOWN_ERROR',
        message: raw.message || detail.detail || error.message || 'An unexpected error occurred',
        details: raw.details || detail || {},
        status: error.response?.status,
        request_id: error.response?.headers?.['x-request-id']
    };

    // 401: Unauthorized -> Logout
    if (error.response?.status === 401 && !originalRequest._retry) {
        if (typeof window !== 'undefined') {
            localStorage.removeItem('admin_token');
            localStorage.removeItem('admin_user');
            // Prevent infinite loop if already on login
            if (!window.location.pathname.includes('/login')) {
                window.location.href = '/login';
            }
        }
    }
    
    // 403: Forbidden -> Optional: Redirect to module-disabled or show toast
    if (error.response?.status === 403) {
        console.warn('Access Forbidden:', standardizedError.message);
    }

    // Attach standardized error to the rejection
    error.standardized = standardizedError;
    return Promise.reject(error);
  }
);

export default api;
