import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

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

    // eslint-disable-next-line no-param-reassign
    config.headers = config.headers || {};

    if (token) {
      // eslint-disable-next-line no-param-reassign
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Owner impersonation: pass tenant context via header
    if (tenantId) {
      // eslint-disable-next-line no-param-reassign
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
    const standardizedError = {
        code: error.response?.data?.error_code || 'UNKNOWN_ERROR',
        message: error.response?.data?.message || error.message || 'An unexpected error occurred',
        details: error.response?.data?.details || {},
        status: error.response?.status
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
